"""
VNStock API Server
==================
FastAPI backend using vnstock as the main data source.

Main capabilities:
- Latest snapshot cache (prefetched at startup)
- Historical OHLCV
- Technical indicators
- Company overview and financial reports
- Company and aggregated market news
- Compatibility routes for existing frontend
"""

import asyncio as _asyncio
import json as _json
import logging
import math
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from vnstock import Company, Finance, Listing, Quote, change_api_key

# ============================================================
# CONFIG
# ============================================================
QUOTE_SOURCE = os.getenv("VNSTOCK_QUOTE_SOURCE", "kbs")
COMPANY_SOURCE = os.getenv("VNSTOCK_COMPANY_SOURCE", "KBS")
FINANCE_SOURCE = os.getenv("VNSTOCK_FINANCE_SOURCE", "kbs")
LISTING_SOURCE = os.getenv("VNSTOCK_LISTING_SOURCE", "kbs")

VNSTOCK_API_KEY = os.getenv("VNSTOCK_API_KEY") or os.getenv("VNAI_API_KEY")
ENABLE_STARTUP_WARMUP = os.getenv("ENABLE_STARTUP_WARMUP", "true").lower() == "true"

DEFAULT_HISTORY_LIMIT = int(os.getenv("DEFAULT_HISTORY_LIMIT", "365"))
SNAPSHOT_REFRESH_SECONDS = int(os.getenv("SNAPSHOT_REFRESH_SECONDS", "900"))
MARKET_REFRESH_SECONDS = int(os.getenv("MARKET_REFRESH_SECONDS", "180"))
NEWS_REFRESH_SECONDS = int(os.getenv("NEWS_REFRESH_SECONDS", "300"))
EVENTS_REFRESH_SECONDS = int(os.getenv("EVENTS_REFRESH_SECONDS", "600"))

VN30_TICKERS = [
    "ACB", "BCM", "BID", "BVH", "CTG",
    "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW",
    "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB",
    "VIC", "VJC", "VNM", "VPB", "VRE",
]

DEFAULT_NEWS_SYMBOLS = ["FPT", "VCB", "HPG", "VNM", "MBB", "TCB", "VIC", "MSN"]
DEFAULT_STARTUP_SYMBOLS = ["FPT", "VNM", "VCB", "HPG", "MBB", "TCB", "VIC", "MSN"]
MAX_STARTUP_SYMBOLS = int(os.getenv("MAX_STARTUP_SYMBOLS", "8"))

DEFAULT_CACHE_DB_PATH = Path(__file__).resolve().parent / "data" / "vnstock_cache.db"
CACHE_DB_PATH = Path(os.getenv("VNSTOCK_CACHE_DB", str(DEFAULT_CACHE_DB_PATH))).expanduser()

MARKET_INDEX_SYMBOLS = ["VNINDEX", "VN30", "HNX", "UPCOM"]
MARKET_INDEX_NAMES = {
    "VNINDEX": "VN-Index",
    "VN30": "VN30",
    "HNX": "HNX-Index",
    "UPCOM": "UPCoM",
}

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(
    title="VNStock API",
    description="VNStock-powered API for OHLCV, technical indicators, financials and news",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# IN-MEMORY CACHES
# ============================================================
_snapshot_cache: dict[str, dict[str, Any]] = {}
_snapshot_cache_time: dict[str, datetime] = {}

_market_index_cache: list[dict[str, Any]] = []
_market_index_cache_time: Optional[datetime] = None

_aggregate_news_cache: dict[str, dict[str, Any]] = {}
_aggregate_events_cache: dict[str, dict[str, Any]] = {}

_cache_lock = _asyncio.Lock()
_db_lock = _asyncio.Lock()
logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _open_cache_db() -> sqlite3.Connection:
    CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _init_cache_db_sync() -> None:
    conn = _open_cache_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_api_cache_updated_at
            ON api_cache(updated_at)
            """
        )
        conn.commit()
    finally:
        conn.close()


def _cache_store_sync(cache_key: str, payload: Any, updated_at: Optional[datetime] = None) -> str:
    stored_at = (updated_at or _now_utc()).isoformat()
    payload_text = _json.dumps(_to_native(payload), ensure_ascii=False, separators=(",", ":"))

    conn = _open_cache_db()
    try:
        conn.execute(
            """
            INSERT INTO api_cache (cache_key, payload, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload = excluded.payload,
                updated_at = excluded.updated_at
            """,
            (cache_key, payload_text, stored_at),
        )
        conn.commit()
        return stored_at
    finally:
        conn.close()


def _cache_load_sync(cache_key: str) -> Optional[dict[str, Any]]:
    conn = _open_cache_db()
    try:
        cursor = conn.execute(
            "SELECT payload, updated_at FROM api_cache WHERE cache_key = ?",
            (cache_key,),
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    payload_text, updated_at = row
    try:
        payload = _json.loads(payload_text)
    except Exception:
        return None

    return {
        "payload": payload,
        "updated_at": updated_at,
    }


async def _init_cache_db() -> None:
    async with _db_lock:
        await _asyncio.to_thread(_init_cache_db_sync)


async def _cache_store(cache_key: str, payload: Any, updated_at: Optional[datetime] = None) -> str:
    async with _db_lock:
        return await _asyncio.to_thread(_cache_store_sync, cache_key, payload, updated_at)


async def _cache_load(cache_key: str) -> Optional[dict[str, Any]]:
    async with _db_lock:
        return await _asyncio.to_thread(_cache_load_sync, cache_key)


def _api_cache_key(name: str, **params: Any) -> str:
    parts = [name]
    for key in sorted(params):
        value = params[key]
        if isinstance(value, list):
            value = ",".join(str(item) for item in value)
        parts.append(f"{key}={value}")
    return "|".join(parts)


def _is_fresh(updated_at: Optional[datetime], ttl_seconds: int) -> bool:
    if updated_at is None:
        return False
    age = (_now_utc() - updated_at).total_seconds()
    return age < ttl_seconds


def _parse_symbols(symbols: Optional[str], fallback: list[str]) -> list[str]:
    if not symbols:
        return list(dict.fromkeys([item.upper() for item in fallback]))

    raw = symbols.replace(";", ",").split(",")
    cleaned = [item.strip().upper() for item in raw if item.strip()]
    return list(dict.fromkeys(cleaned)) or list(dict.fromkeys([item.upper() for item in fallback]))


def _to_native(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().isoformat()

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    if isinstance(value, dict):
        return {key: _to_native(val) for key, val in value.items()}

    if isinstance(value, (list, tuple)):
        return [_to_native(item) for item in value]

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


def _to_float(value: Any, fallback: float = 0.0) -> float:
    native = _to_native(value)
    if native is None:
        return fallback

    if isinstance(native, (int, float)):
        return float(native)

    if isinstance(native, str):
        try:
            return float(native.replace(",", ""))
        except ValueError:
            return fallback

    return fallback


def _to_int(value: Any, fallback: int = 0) -> int:
    native = _to_native(value)
    if native is None:
        return fallback

    if isinstance(native, int):
        return native

    if isinstance(native, float):
        return int(native)

    if isinstance(native, str):
        try:
            return int(float(native.replace(",", "")))
        except ValueError:
            return fallback

    return fallback


def _to_iso_time(value: Any, fallback: str = "") -> str:
    native = _to_native(value)
    if native is None:
        return fallback

    if isinstance(native, str):
        return native

    if isinstance(native, datetime):
        return native.isoformat()

    return str(native)


def _to_datetime_sort_key(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if isinstance(value, pd.Timestamp):
        dt = value.to_pydatetime()
        return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return datetime(1970, 1, 1, tzinfo=timezone.utc)

        for converted in (
            candidate,
            candidate.replace("Z", "+00:00"),
            candidate.replace(" ", "T"),
        ):
            try:
                dt = datetime.fromisoformat(converted)
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _with_response_meta(payload: dict[str, Any], source: str, last_synced_at: Optional[str]) -> dict[str, Any]:
    enriched = dict(payload)
    enriched["source"] = source
    if last_synced_at:
        enriched["last_synced_at"] = last_synced_at
    return enriched


def _latest_snapshot_sync_time(snapshots: list[dict[str, Any]]) -> str:
    candidates = [item.get("syncedAt") for item in snapshots if item.get("syncedAt")]
    if not candidates:
        return ""

    latest = max(candidates, key=_to_datetime_sort_key)
    return _to_iso_time(latest, "")


async def _cached_response_payload(cache_key: str, source: str = "database") -> Optional[dict[str, Any]]:
    cached = await _cache_load(cache_key)
    if not cached:
        return None

    payload = cached.get("payload")
    if not isinstance(payload, dict):
        return None

    return _with_response_meta(payload, source, cached.get("updated_at"))


def _configure_vnstock_api_key() -> None:
    if not VNSTOCK_API_KEY:
        return

    try:
        changed = change_api_key(VNSTOCK_API_KEY)
        if changed:
            logger.info("VNStock API key configured from environment")
    except BaseException as exc:
        logger.warning("Failed to configure VNStock API key from environment: %s", exc)


def _company_name_from_overview(overview: dict[str, Any], symbol: str) -> str:
    keys = [
        "company_name", "companyName", "name", "company", "short_name",
        "organ_name", "symbol_name", "stock_name",
    ]
    for key in keys:
        value = overview.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return symbol


def _empty_snapshot(symbol: str, company_name: Optional[str] = None) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "companyName": company_name or symbol,
        "price": 0.0,
        "change": 0.0,
        "changePercent": 0.0,
        "volume": 0,
        "high": 0.0,
        "low": 0.0,
        "open": 0.0,
        "refPrice": 0.0,
        "lastUpdate": _now_utc().isoformat(),
        "syncedAt": None,
    }


def _fetch_history_dataframe(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
    interval: str = "1D",
) -> pd.DataFrame:
    try:
        quote = Quote(source=QUOTE_SOURCE, symbol=symbol)

        if start_date or end_date:
            df = quote.history(start=start_date, end=end_date, interval=interval)
        else:
            length = limit if limit and limit > 0 else DEFAULT_HISTORY_LIMIT
            df = quote.history(length=length, interval=interval)
    except BaseException as exc:
        raise RuntimeError(f"History fetch failed for {symbol}: {exc}") from None

    if df is None or df.empty:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

    for col in ["time", "open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            df[col] = np.nan

    df = df[["time", "open", "high", "low", "close", "volume"]].copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time")

    if limit and limit > 0:
        df = df.tail(limit)

    return df.reset_index(drop=True)


def _fetch_company_overview(symbol: str) -> dict[str, Any]:
    try:
        company = Company(source=COMPANY_SOURCE, symbol=symbol)
        overview_df = company.overview()
    except BaseException as exc:
        raise RuntimeError(f"Overview fetch failed for {symbol}: {exc}") from None

    if overview_df is None or overview_df.empty:
        raise ValueError(f"No company overview for {symbol}")

    row = overview_df.iloc[0].to_dict()
    return {key: _to_native(value) for key, value in row.items()}


def _build_snapshot(
    symbol: str,
    history_df: pd.DataFrame,
    overview: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    overview = overview or {}

    if history_df is None or history_df.empty:
        return _empty_snapshot(symbol, _company_name_from_overview(overview, symbol))

    latest = history_df.iloc[-1]
    previous = history_df.iloc[-2] if len(history_df) > 1 else latest

    latest_close = _to_float(latest.get("close"))
    latest_open = _to_float(latest.get("open"), latest_close)
    previous_close = _to_float(previous.get("close"), latest_open)

    ref_price = previous_close if previous_close > 0 else latest_open
    change = latest_close - ref_price
    change_percent = (change / ref_price * 100.0) if ref_price > 0 else 0.0

    return {
        "symbol": symbol,
        "companyName": _company_name_from_overview(overview, symbol),
        "price": latest_close,
        "change": change,
        "changePercent": change_percent,
        "volume": _to_int(latest.get("volume")),
        "high": _to_float(latest.get("high"), latest_close),
        "low": _to_float(latest.get("low"), latest_close),
        "open": latest_open,
        "refPrice": ref_price,
        "lastUpdate": _to_iso_time(latest.get("time"), _now_utc().isoformat()),
    }


def _fetch_snapshot(symbol: str, include_overview: bool = False) -> dict[str, Any]:
    history_df = _fetch_history_dataframe(symbol=symbol, limit=2)
    if history_df.empty:
        raise RuntimeError(f"No snapshot data for {symbol}")

    overview: dict[str, Any] = {}
    if include_overview:
        try:
            overview = _fetch_company_overview(symbol)
        except BaseException:
            overview = {}

    return _build_snapshot(symbol=symbol, history_df=history_df, overview=overview)


def _history_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        records.append(
            {
                "time": _to_iso_time(row.get("time")),
                "open": _to_float(row.get("open")),
                "high": _to_float(row.get("high")),
                "low": _to_float(row.get("low")),
                "close": _to_float(row.get("close")),
                "volume": _to_int(row.get("volume")),
            }
        )
    return records


# ============================================================
# TECHNICAL INDICATORS
# ============================================================
def calc_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=1).mean()


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def calc_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = calc_ema(series, fast)
    ema_slow = calc_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calc_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    sma = calc_sma(series, period)
    rolling_std = series.rolling(window=period, min_periods=1).std(ddof=0)
    upper = sma + (rolling_std * std_dev)
    lower = sma - (rolling_std * std_dev)
    return upper, sma, lower


def calc_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
):
    lowest_low = low.rolling(window=k_period, min_periods=1).min()
    highest_high = high.rolling(window=k_period, min_periods=1).max()
    denom = highest_high - lowest_low
    k = 100 * (close - lowest_low) / denom.replace(0, np.nan)
    k = k.fillna(50)
    d = k.rolling(window=d_period, min_periods=1).mean()
    return k, d


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def calc_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (volume * direction).cumsum()


def compute_technical_indicators(df: pd.DataFrame) -> dict[str, list[float]]:
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)

    sma_20 = calc_sma(close, 20)
    sma_50 = calc_sma(close, 50)
    sma_200 = calc_sma(close, 200)
    ema_12 = calc_ema(close, 12)
    ema_26 = calc_ema(close, 26)

    rsi_14 = calc_rsi(close, 14)
    macd_line, signal_line, macd_hist = calc_macd(close)

    bb_upper, bb_middle, bb_lower = calc_bollinger_bands(close)

    stoch_k, stoch_d = calc_stochastic(high, low, close)
    atr_14 = calc_atr(high, low, close)
    obv = calc_obv(close, volume)

    return {
        "sma_20": sma_20.round(2).tolist(),
        "sma_50": sma_50.round(2).tolist(),
        "sma_200": sma_200.round(2).tolist(),
        "ema_12": ema_12.round(2).tolist(),
        "ema_26": ema_26.round(2).tolist(),
        "rsi_14": rsi_14.round(2).tolist(),
        "macd_line": macd_line.round(2).tolist(),
        "macd_signal": signal_line.round(2).tolist(),
        "macd_histogram": macd_hist.round(2).tolist(),
        "bb_upper": bb_upper.round(2).tolist(),
        "bb_middle": bb_middle.round(2).tolist(),
        "bb_lower": bb_lower.round(2).tolist(),
        "stoch_k": stoch_k.round(2).tolist(),
        "stoch_d": stoch_d.round(2).tolist(),
        "atr_14": atr_14.round(2).tolist(),
        "obv": obv.round(0).tolist(),
    }


def _summarize_signals(
    rsi: float,
    macd: float,
    signal: float,
    sma50: float,
    sma200: float,
    close: float,
) -> str:
    score = 0

    if rsi < 30:
        score += 2
    elif rsi > 70:
        score -= 2
    elif rsi < 50:
        score -= 1
    else:
        score += 1

    if macd > signal:
        score += 1
    else:
        score -= 1

    if sma50 > sma200:
        score += 1
    else:
        score -= 1

    if close > sma200:
        score += 1
    else:
        score -= 1

    if score >= 3:
        return "strong_buy"
    if score >= 1:
        return "buy"
    if score <= -3:
        return "strong_sell"
    if score <= -1:
        return "sell"
    return "neutral"


def _technical_payload(symbol: str, df: pd.DataFrame) -> dict[str, Any]:
    work = df.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)

    indicators = compute_technical_indicators(work)

    ohlcv = {
        "time": [_to_iso_time(value) for value in work["time"].tolist()],
        "open": work["open"].astype(float).tolist(),
        "high": work["high"].astype(float).tolist(),
        "low": work["low"].astype(float).tolist(),
        "close": work["close"].astype(float).tolist(),
        "volume": work["volume"].astype(float).astype(int).tolist(),
    }

    close = work["close"].astype(float)
    last_close = float(close.iloc[-1])

    last_rsi = float(indicators["rsi_14"][-1])
    last_macd = float(indicators["macd_line"][-1])
    last_signal = float(indicators["macd_signal"][-1])
    last_sma_50 = float(indicators["sma_50"][-1])
    last_sma_200 = float(indicators["sma_200"][-1])

    signals = {
        "rsi": "oversold" if last_rsi < 30 else ("overbought" if last_rsi > 70 else "neutral"),
        "macd": "bullish" if last_macd > last_signal else "bearish",
        "golden_cross": last_sma_50 > last_sma_200,
        "price_vs_sma200": "above" if last_close > last_sma_200 else "below",
        "summary": _summarize_signals(
            rsi=last_rsi,
            macd=last_macd,
            signal=last_signal,
            sma50=last_sma_50,
            sma200=last_sma_200,
            close=last_close,
        ),
    }

    return {
        "symbol": symbol,
        "count": int(len(work)),
        "ohlcv": ohlcv,
        "indicators": indicators,
        "signals": signals,
    }


def _fetch_financials(symbol: str, report_type: str, period: str) -> list[dict[str, Any]]:
    try:
        finance = Finance(source=FINANCE_SOURCE, symbol=symbol)

        if report_type == "income":
            df = finance.income_statement(period=period)
        elif report_type == "balance":
            df = finance.balance_sheet(period=period)
        elif report_type == "cashflow":
            df = finance.cash_flow(period=period)
        elif report_type == "ratios":
            df = finance.ratio(period=period)
        else:
            raise ValueError(f"Invalid report_type: {report_type}")
    except BaseException as exc:
        raise RuntimeError(f"Financial data failed for {symbol}: {exc}") from None

    if df is None or df.empty:
        return []

    df = df.where(pd.notna(df), None)
    records = df.to_dict(orient="records")
    return [{key: _to_native(value) for key, value in row.items()} for row in records]


def _fetch_market_indices_sync() -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = []

    for symbol in MARKET_INDEX_SYMBOLS:
        try:
            df = _fetch_history_dataframe(symbol=symbol, limit=2)
            if df.empty:
                continue

            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest

            close_value = _to_float(latest.get("close"))
            previous_close = _to_float(previous.get("close"), close_value)
            change_value = close_value - previous_close
            change_percent = (change_value / previous_close * 100.0) if previous_close > 0 else 0.0

            data.append(
                {
                    "index_name": MARKET_INDEX_NAMES.get(symbol, symbol),
                    "symbol": symbol,
                    "close": close_value,
                    "change": change_value,
                    "change_percent": change_percent,
                    "time": _to_iso_time(latest.get("time")),
                }
            )
        except BaseException:
            continue

    return data


def _infer_impact(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()

    high_keywords = ["profit", "loss", "bankrupt", "merger", "acquisition", "dividend", "earnings"]
    medium_keywords = ["forecast", "plan", "guidance", "target", "investment", "upgrade", "downgrade"]

    if any(keyword in text for keyword in high_keywords):
        return "high"
    if any(keyword in text for keyword in medium_keywords):
        return "medium"
    return "low"


def _normalize_news_item(symbol: str, row: dict[str, Any], index: int) -> Optional[dict[str, Any]]:
    title = str(row.get("title") or row.get("head") or "").strip()
    if not title:
        return None

    summary = str(
        row.get("short_description")
        or row.get("description")
        or row.get("head")
        or title
    ).strip()

    raw_url = str(row.get("url") or "").strip()
    parsed_source = ""
    if raw_url:
        parsed = urlparse(raw_url)
        parsed_source = parsed.netloc.replace("www.", "") if parsed.netloc else ""

    publish_time = _to_iso_time(row.get("publish_time"), _now_utc().isoformat())
    article_id = _to_native(row.get("article_id"))

    stable_id = f"{symbol}-{article_id or index}"
    impact = _infer_impact(title, summary)

    return {
        "id": stable_id,
        "symbol": symbol,
        "symbols": [symbol],
        "source": parsed_source or "vnstock",
        "title": title,
        "summary": summary,
        "publish_time": publish_time,
        "time": publish_time,
        "url": raw_url,
        "impact": impact,
    }


def _news_from_company(symbol: str, limit: int = 10) -> list[dict[str, Any]]:
    try:
        company = Company(source=COMPANY_SOURCE, symbol=symbol)
        news_df = company.news()
    except BaseException:
        return []

    if news_df is None or news_df.empty:
        return []

    news_df = news_df.where(pd.notna(news_df), None)
    raw_rows = news_df.to_dict(orient="records")

    items: list[dict[str, Any]] = []
    for idx, row in enumerate(raw_rows):
        item = _normalize_news_item(symbol=symbol, row=row, index=idx)
        if item:
            items.append(item)

    items.sort(key=lambda item: _to_datetime_sort_key(item.get("publish_time")), reverse=True)
    return items[:limit]


def _events_from_company(symbol: str, limit: int = 10) -> list[dict[str, Any]]:
    try:
        company = Company(source=COMPANY_SOURCE, symbol=symbol)
        events_df = company.events()
    except BaseException:
        return []

    if events_df is None or events_df.empty:
        return []

    events_df = events_df.where(pd.notna(events_df), None)
    rows = events_df.to_dict(orient="records")

    def _pick(row: dict[str, Any], keys: list[str]) -> str:
        for key in keys:
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if value is not None and not isinstance(value, (list, dict)):
                text = str(value).strip()
                if text:
                    return text
        return ""

    items: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        title = _pick(row, ["title", "event", "event_title", "name", "head"])
        if not title:
            title = f"Corporate event #{index + 1}"

        date_text = _pick(row, ["event_date", "date", "publish_time", "time", "ex_right_date"])
        description = _pick(row, ["description", "content", "detail", "event_type", "type"]) or "Corporate event"

        iso_date = _to_iso_time(date_text, date_text)
        short_date = iso_date[:10] if iso_date else ""

        items.append(
            {
                "id": f"{symbol}-event-{index}",
                "symbol": symbol,
                "date": short_date,
                "title": title,
                "description": description,
            }
        )

    items.sort(key=lambda item: item.get("date") or "")
    return items[:limit]


# ============================================================
# CACHE LOADERS
# ============================================================
async def _get_snapshots(symbols: list[str], force: bool = False) -> list[dict[str, Any]]:
    symbols = [item.upper() for item in symbols]
    to_refresh: list[str] = []

    async with _cache_lock:
        for symbol in symbols:
            if force or not _is_fresh(_snapshot_cache_time.get(symbol), SNAPSHOT_REFRESH_SECONDS):
                to_refresh.append(symbol)

    refreshed: dict[str, dict[str, Any]] = {}
    if to_refresh:
        results = await _asyncio.gather(
            *[_asyncio.to_thread(_fetch_snapshot, symbol, False) for symbol in to_refresh],
            return_exceptions=True,
        )

        now = _now_utc()
        async with _cache_lock:
            for symbol, result in zip(to_refresh, results):
                if isinstance(result, BaseException):
                    continue
                snapshot = dict(result)
                snapshot["syncedAt"] = now.isoformat()
                _snapshot_cache[symbol] = snapshot
                _snapshot_cache_time[symbol] = now
                refreshed[symbol] = snapshot

    if refreshed:
        await _asyncio.gather(
            *[
                _cache_store(
                    _api_cache_key("snapshot", symbol=symbol),
                    snapshot,
                    _to_datetime_sort_key(snapshot.get("syncedAt")),
                )
                for symbol, snapshot in refreshed.items()
            ],
            return_exceptions=True,
        )

    snapshots_by_symbol: dict[str, dict[str, Any]] = {}
    missing_symbols: list[str] = []

    async with _cache_lock:
        for symbol in symbols:
            item = _snapshot_cache.get(symbol)
            if item:
                snapshots_by_symbol[symbol] = item
            else:
                missing_symbols.append(symbol)

    recovered: dict[str, dict[str, Any]] = {}
    for symbol in missing_symbols:
        cached = await _cache_load(_api_cache_key("snapshot", symbol=symbol))
        if not cached:
            continue

        payload = cached.get("payload")
        if isinstance(payload, dict):
            recovered[symbol] = payload
            snapshots_by_symbol[symbol] = payload

    if recovered:
        async with _cache_lock:
            for symbol, payload in recovered.items():
                _snapshot_cache[symbol] = payload
                _snapshot_cache_time[symbol] = _to_datetime_sort_key(
                    payload.get("syncedAt") or payload.get("lastUpdate")
                )

    return [snapshots_by_symbol.get(symbol, _empty_snapshot(symbol)) for symbol in symbols]


async def _get_market_indices(force: bool = False) -> list[dict[str, Any]]:
    global _market_index_cache_time
    db_cache_key = _api_cache_key("market_indices")

    async with _cache_lock:
        if not force and _is_fresh(_market_index_cache_time, MARKET_REFRESH_SECONDS):
            return list(_market_index_cache)

    try:
        fresh_data = await _asyncio.to_thread(_fetch_market_indices_sync)
    except BaseException:
        fresh_data = []

    if fresh_data:
        synced_at = _now_utc()
        await _cache_store(db_cache_key, {"data": fresh_data}, synced_at)

        async with _cache_lock:
            _market_index_cache.clear()
            _market_index_cache.extend(fresh_data)
            _market_index_cache_time = synced_at

        return list(fresh_data)

    cached = await _cache_load(db_cache_key)
    if cached and isinstance(cached.get("payload"), dict):
        payload = cached["payload"]
        items = payload.get("data")
        if isinstance(items, list):
            async with _cache_lock:
                _market_index_cache.clear()
                _market_index_cache.extend(items)
                _market_index_cache_time = _to_datetime_sort_key(cached.get("updated_at"))
            return list(items)

    return []


def _cache_key(prefix: str, symbols: list[str], limit: int) -> str:
    return f"{prefix}:{','.join(symbols)}:{limit}"


async def _aggregate_news(symbols: list[str], limit: int, force: bool = False) -> list[dict[str, Any]]:
    cache_key = _cache_key("news", symbols, limit)
    db_cache_key = _api_cache_key("aggregate_news", symbols=symbols, limit=limit)
    stale_items: list[dict[str, Any]] = []

    async with _cache_lock:
        cached = _aggregate_news_cache.get(cache_key)
        if cached and not force and _is_fresh(cached.get("updated_at"), NEWS_REFRESH_SECONDS):
            return list(cached.get("items", []))
        if cached:
            stale_items = list(cached.get("items", []))

    per_symbol_limit = max(3, min(limit, int(math.ceil(limit / max(1, len(symbols)))) + 2))
    results = await _asyncio.gather(
        *[_asyncio.to_thread(_news_from_company, symbol, per_symbol_limit) for symbol in symbols],
        return_exceptions=True,
    )

    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for symbol, result in zip(symbols, results):
        if isinstance(result, BaseException):
            continue

        for item in result:
            dedupe_key = (
                str(item.get("url") or ""),
                str(item.get("title") or ""),
                symbol,
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            merged.append(item)

    merged.sort(key=lambda item: _to_datetime_sort_key(item.get("publish_time")), reverse=True)
    merged = merged[:limit]

    if merged:
        synced_at = _now_utc()

        async with _cache_lock:
            _aggregate_news_cache[cache_key] = {
                "updated_at": synced_at,
                "items": merged,
            }

        await _cache_store(db_cache_key, {"items": merged}, synced_at)
        return merged

    if stale_items:
        return stale_items

    cached_db = await _cache_load(db_cache_key)
    if cached_db and isinstance(cached_db.get("payload"), dict):
        items = cached_db["payload"].get("items")
        if isinstance(items, list):
            return list(items)

    return []


async def _aggregate_events(symbols: list[str], limit: int, force: bool = False) -> list[dict[str, Any]]:
    cache_key = _cache_key("events", symbols, limit)
    db_cache_key = _api_cache_key("aggregate_events", symbols=symbols, limit=limit)
    stale_items: list[dict[str, Any]] = []

    async with _cache_lock:
        cached = _aggregate_events_cache.get(cache_key)
        if cached and not force and _is_fresh(cached.get("updated_at"), EVENTS_REFRESH_SECONDS):
            return list(cached.get("items", []))
        if cached:
            stale_items = list(cached.get("items", []))

    per_symbol_limit = max(2, min(limit, int(math.ceil(limit / max(1, len(symbols)))) + 1))
    results = await _asyncio.gather(
        *[_asyncio.to_thread(_events_from_company, symbol, per_symbol_limit) for symbol in symbols],
        return_exceptions=True,
    )

    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for symbol, result in zip(symbols, results):
        if isinstance(result, BaseException):
            continue

        for item in result:
            dedupe_key = (
                str(item.get("date") or ""),
                str(item.get("title") or ""),
                symbol,
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            merged.append(item)

    merged.sort(key=lambda item: item.get("date") or "")
    merged = merged[:limit]

    if merged:
        synced_at = _now_utc()

        async with _cache_lock:
            _aggregate_events_cache[cache_key] = {
                "updated_at": synced_at,
                "items": merged,
            }

        await _cache_store(db_cache_key, {"items": merged}, synced_at)
        return merged

    if stale_items:
        return stale_items

    cached_db = await _cache_load(db_cache_key)
    if cached_db and isinstance(cached_db.get("payload"), dict):
        items = cached_db["payload"].get("items")
        if isinstance(items, list):
            return list(items)

    return []


@app.on_event("startup")
async def warm_start_cache() -> None:
    try:
        await _init_cache_db()
    except BaseException as exc:
        logger.warning("Cache database initialization failed: %s", exc)

    _configure_vnstock_api_key()

    if not ENABLE_STARTUP_WARMUP:
        return

    startup_symbols = _parse_symbols(os.getenv("VNSTOCK_STARTUP_SYMBOLS"), DEFAULT_STARTUP_SYMBOLS)
    startup_symbols = startup_symbols[:max(1, MAX_STARTUP_SYMBOLS)]

    try:
        await _get_snapshots(startup_symbols, force=True)
    except BaseException as exc:
        logger.warning("Startup snapshot warmup skipped: %s", exc)

    try:
        await _get_market_indices(force=True)
    except BaseException as exc:
        logger.warning("Startup market-index warmup skipped: %s", exc)


# ============================================================
# API ROUTES
# ============================================================
@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "VNStock API",
        "version": "2.0.0",
        "provider": "vnstock",
    }


@app.get("/api/health")
async def health() -> dict[str, str]:
    try:
        df = await _asyncio.to_thread(_fetch_history_dataframe, "FPT", None, None, 1, "1D")
        if df.empty:
            raise RuntimeError("No data returned from vnstock")
        return {"status": "ok", "database": "vnstock-connected"}
    except BaseException as exc:
        return {"status": "error", "database": str(exc)}


@app.get("/api/stocks")
async def get_stocks(
    scope: str = Query("vn30", pattern="^(vn30|all)$"),
    limit: int = Query(2000, ge=1, le=5000),
) -> dict[str, Any]:
    cache_key = _api_cache_key("stocks", scope=scope, limit=limit)

    if scope == "all":
        try:
            listing = Listing(source=LISTING_SOURCE)
            symbols_df = await _asyncio.to_thread(listing.all_symbols)
            if symbols_df is None or symbols_df.empty:
                raise RuntimeError("No symbols returned from listing provider")

            symbols = []
            for value in symbols_df.get("symbol", pd.Series(dtype="object")).tolist():
                text = str(value).strip().upper()
                if text:
                    symbols.append(text)

            payload = {"tickers": list(dict.fromkeys(symbols))[:limit]}
            synced_at = await _cache_store(cache_key, payload)
            return _with_response_meta(payload, "live", synced_at)
        except BaseException:
            cached = await _cached_response_payload(cache_key)
            if cached:
                return cached

            fallback = {"tickers": VN30_TICKERS}
            return _with_response_meta(fallback, "default", None)

    payload = {"tickers": VN30_TICKERS}
    return _with_response_meta(payload, "default", None)


@app.get("/api/stocks/snapshots")
async def get_stock_snapshots(
    symbols: Optional[str] = Query(None, description="Comma-separated symbols"),
    refresh: bool = Query(False),
) -> dict[str, Any]:
    symbol_list = _parse_symbols(symbols, VN30_TICKERS)
    cache_key = _api_cache_key("snapshots", symbols=symbol_list)

    try:
        snapshots = await _get_snapshots(symbol_list, force=refresh)
        latest_sync = _latest_snapshot_sync_time(snapshots)
        payload = {
            "count": len(snapshots),
            "data": snapshots,
            "cached_at": latest_sync,
        }
        store_time = _to_datetime_sort_key(latest_sync) if latest_sync else _now_utc()
        synced_at = await _cache_store(cache_key, payload, store_time)
        return _with_response_meta(payload, "live_or_cache", latest_sync or synced_at)
    except BaseException as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached
        raise HTTPException(status_code=502, detail=f"Snapshot fetch failed: {exc}")


@app.get("/api/stocks/{symbol}/overview")
async def get_stock_overview(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper()
    cache_key = _api_cache_key("overview", symbol=symbol)

    try:
        payload = await _asyncio.to_thread(_fetch_company_overview, symbol)
        synced_at = await _cache_store(cache_key, payload)
        return _with_response_meta(payload, "live", synced_at)
    except Exception as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached
        raise HTTPException(status_code=502, detail=f"Overview fetch failed for {symbol}: {exc}")


@app.get("/api/stocks/{symbol}/history")
async def get_stock_history(
    symbol: str,
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(DEFAULT_HISTORY_LIMIT, ge=1, le=5000),
) -> dict[str, Any]:
    symbol = symbol.upper()
    cache_key = _api_cache_key(
        "history",
        symbol=symbol,
        start=start_date or "",
        end=end_date or "",
        limit=limit,
    )

    try:
        df = await _asyncio.to_thread(_fetch_history_dataframe, symbol, start_date, end_date, limit, "1D")
        if df.empty:
            raise ValueError(f"No historical data for {symbol}")

        records = _history_records(df)
        payload = {"symbol": symbol, "count": len(records), "data": records}
        synced_at = await _cache_store(cache_key, payload)
        return _with_response_meta(payload, "live", synced_at)
    except Exception as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached

        if isinstance(exc, ValueError):
            raise HTTPException(status_code=404, detail=str(exc))

        raise HTTPException(status_code=502, detail=f"History fetch failed for {symbol}: {exc}")


@app.get("/api/stocks/{symbol}/technical")
async def get_technical_analysis(
    symbol: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(DEFAULT_HISTORY_LIMIT, ge=50, le=5000),
) -> dict[str, Any]:
    symbol = symbol.upper()
    cache_key = _api_cache_key(
        "technical",
        symbol=symbol,
        start=start_date or "",
        end=end_date or "",
        limit=limit,
    )

    try:
        df = await _asyncio.to_thread(_fetch_history_dataframe, symbol, start_date, end_date, limit, "1D")
        if df.empty:
            raise ValueError(f"No data for {symbol}")

        payload = _technical_payload(symbol=symbol, df=df)
        synced_at = await _cache_store(cache_key, payload)
        return _with_response_meta(payload, "live", synced_at)
    except Exception as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached

        if isinstance(exc, ValueError):
            raise HTTPException(status_code=404, detail=str(exc))

        raise HTTPException(status_code=502, detail=f"Technical analysis failed for {symbol}: {exc}")


@app.get("/api/stocks/{symbol}/financials")
async def get_financial_data(
    symbol: str,
    report_type: str = Query("income", pattern="^(income|balance|cashflow|ratios)$"),
    period: str = Query("quarter", pattern="^(quarter|year)$"),
) -> dict[str, Any]:
    symbol = symbol.upper()
    cache_key = _api_cache_key("financials", symbol=symbol, report_type=report_type, period=period)

    try:
        records = await _asyncio.to_thread(_fetch_financials, symbol, report_type, period)
        payload = {
            "symbol": symbol,
            "type": report_type,
            "period": period,
            "count": len(records),
            "data": records,
        }
        synced_at = await _cache_store(cache_key, payload)
        return _with_response_meta(payload, "live", synced_at)
    except Exception as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached
        raise HTTPException(status_code=502, detail=f"Financial data failed for {symbol}: {exc}")


@app.get("/api/market-indices")
async def get_market_indices(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    _ = (start_date, end_date)  # kept for compatibility with existing frontend contract
    cache_key = _api_cache_key("market_indices_endpoint", limit=limit)

    try:
        data = await _get_market_indices(force=False)
        sliced = data[:limit]
        payload = {"count": len(sliced), "data": sliced}

        if sliced:
            synced_at = await _cache_store(cache_key, payload)
            return _with_response_meta(payload, "live", synced_at)

        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached

        return _with_response_meta(payload, "empty", None)
    except Exception as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached
        raise HTTPException(status_code=502, detail=f"Market indices fetch failed: {exc}")


@app.get("/api/stocks/{symbol}/news")
async def get_stock_news(
    symbol: str,
    limit: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    symbol = symbol.upper()
    cache_key = _api_cache_key("stock_news", symbol=symbol, limit=limit)

    try:
        items = await _asyncio.to_thread(_news_from_company, symbol, limit)
        payload = {"symbol": symbol, "count": len(items), "data": items}

        if items:
            synced_at = await _cache_store(cache_key, payload)
            return _with_response_meta(payload, "live", synced_at)

        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached

        return _with_response_meta(payload, "empty", None)
    except Exception as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached
        raise HTTPException(status_code=502, detail=f"News fetch failed for {symbol}: {exc}")


@app.get("/api/stocks/{symbol}/events")
async def get_stock_events(
    symbol: str,
    limit: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    symbol = symbol.upper()
    cache_key = _api_cache_key("stock_events", symbol=symbol, limit=limit)

    try:
        items = await _asyncio.to_thread(_events_from_company, symbol, limit)
        payload = {"symbol": symbol, "count": len(items), "data": items}

        if items:
            synced_at = await _cache_store(cache_key, payload)
            return _with_response_meta(payload, "live", synced_at)

        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached

        return _with_response_meta(payload, "empty", None)
    except Exception as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached
        raise HTTPException(status_code=502, detail=f"Events fetch failed for {symbol}: {exc}")


@app.get("/api/news")
async def get_market_news(
    symbols: Optional[str] = Query(None, description="Comma-separated symbols"),
    limit: int = Query(24, ge=1, le=200),
    refresh: bool = Query(False),
) -> dict[str, Any]:
    symbol_list = _parse_symbols(symbols, DEFAULT_NEWS_SYMBOLS)
    cache_key = _api_cache_key("market_news", symbols=symbol_list, limit=limit)

    try:
        items = await _aggregate_news(symbols=symbol_list, limit=limit, force=refresh)
        payload = {
            "count": len(items),
            "symbols": symbol_list,
            "data": items,
            "cached_at": _now_utc().isoformat(),
        }

        if items:
            synced_at = await _cache_store(cache_key, payload)
            return _with_response_meta(payload, "live", synced_at)

        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached

        return _with_response_meta(payload, "empty", None)
    except Exception as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached
        raise HTTPException(status_code=502, detail=f"Aggregated news fetch failed: {exc}")


@app.get("/api/events")
async def get_market_events(
    symbols: Optional[str] = Query(None, description="Comma-separated symbols"),
    limit: int = Query(24, ge=1, le=200),
    refresh: bool = Query(False),
) -> dict[str, Any]:
    symbol_list = _parse_symbols(symbols, DEFAULT_NEWS_SYMBOLS)
    cache_key = _api_cache_key("market_events", symbols=symbol_list, limit=limit)

    try:
        items = await _aggregate_events(symbols=symbol_list, limit=limit, force=refresh)
        payload = {
            "count": len(items),
            "symbols": symbol_list,
            "data": items,
            "cached_at": _now_utc().isoformat(),
        }

        if items:
            synced_at = await _cache_store(cache_key, payload)
            return _with_response_meta(payload, "live", synced_at)

        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached

        return _with_response_meta(payload, "empty", None)
    except Exception as exc:
        cached = await _cached_response_payload(cache_key)
        if cached:
            return cached
        raise HTTPException(status_code=502, detail=f"Aggregated events fetch failed: {exc}")


@app.post("/api/dnse/save-quotes")
async def save_dnse_quotes(quotes: list[dict[str, Any]]) -> dict[str, Any]:
    if not quotes:
        return {"saved": 0, "mode": "snapshot-cache"}

    now = _now_utc()
    now_iso = now.isoformat()
    saved = 0
    store_tasks: list[Any] = []

    for quote in quotes:
        symbol = str(quote.get("symbol") or "").strip().upper()
        if not symbol:
            continue

        price = _to_float(quote.get("price"))
        change = _to_float(quote.get("change"))
        change_percent = _to_float(quote.get("changePercent"))
        open_price = _to_float(quote.get("open"), max(price - change, 0.0))
        ref_price = _to_float(quote.get("refPrice"), price - change)

        snapshot = {
            "symbol": symbol,
            "companyName": symbol,
            "price": price,
            "change": change,
            "changePercent": change_percent,
            "volume": _to_int(quote.get("volume")),
            "high": _to_float(quote.get("high"), price),
            "low": _to_float(quote.get("low"), price),
            "open": open_price,
            "refPrice": ref_price,
            "lastUpdate": _to_iso_time(quote.get("time"), now_iso),
            "syncedAt": now_iso,
        }

        async with _cache_lock:
            existing = _snapshot_cache.get(symbol, {})
            company_name = existing.get("companyName") if isinstance(existing, dict) else None
            if isinstance(company_name, str) and company_name.strip():
                snapshot["companyName"] = company_name

            _snapshot_cache[symbol] = snapshot
            _snapshot_cache_time[symbol] = now

        store_tasks.append(_cache_store(_api_cache_key("snapshot", symbol=symbol), snapshot, now))
        saved += 1

    if store_tasks:
        await _asyncio.gather(*store_tasks, return_exceptions=True)

    return {"saved": saved, "mode": "snapshot-cache"}


@app.websocket("/api/ws/dnse")
async def websocket_dnse_proxy(websocket: WebSocket) -> None:
    # Realtime is intentionally disabled for now.
    await websocket.accept()
    await websocket.send_text(
        _json.dumps(
            {
                "type": "info",
                "message": "Realtime stream is disabled. Use REST snapshots/history endpoints.",
            }
        )
    )
    await websocket.close(code=1000)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
