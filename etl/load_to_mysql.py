"""Load processed/raw ETL outputs into MySQL cache tables."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from etl.config import FUNDAMENTAL_REPORT_TYPES, EtlConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


def get_engine():
    env_path = Path("backend_v2/.env")
    if env_path.exists():
        load_dotenv(env_path)

    mysql_url = os.getenv("MYSQL_URL")
    if not mysql_url:
        mysql_url = "mysql+mysqlconnector://root:123456789@localhost/vnstock_data"
        log.warning("MYSQL_URL not found in %s, using default: %s", env_path, mysql_url)
    return create_engine(mysql_url)


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clean_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean_json(item) for item in value]
    if isinstance(value, tuple):
        return [_clean_json(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _json_dumps(payload: Any) -> str:
    return json.dumps(_clean_json(payload), ensure_ascii=False, default=str)


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log.warning("Invalid JSON skipped: %s", path)
        return None


def _raw_json_path(cfg: EtlConfig, category: str, symbol: str) -> Path:
    return cfg.raw_dir / category / symbol.upper() / f"{cfg.run_id}.json"


def _latest_processed_parquet(cfg: EtlConfig | None = None) -> Path | None:
    processed_dir = cfg.processed_dir if cfg else Path("lake/processed")
    files = sorted(processed_dir.glob("market_data_*.parquet"))
    return files[-1] if files else None


def load_daily_price(cfg: EtlConfig | None = None, dataset: pd.DataFrame | None = None) -> int:
    engine = get_engine()
    if dataset is None:
        latest_file = _latest_processed_parquet(cfg)
        if not latest_file:
            log.error("No parquet files found in processed dir")
            return 0
        log.info("Loading prices from: %s", latest_file)
        dataset = pd.read_parquet(latest_file)

    ohlcv_cols = ["symbol", "data_date", "open_price", "high_price", "low_price", "close_price", "volume"]
    if not all(col in dataset.columns for col in ohlcv_cols):
        log.error("Missing required OHLCV columns in dataset")
        return 0

    df = dataset[ohlcv_cols].copy()
    df = df.rename(
        columns={
            "data_date": "date",
            "open_price": "open",
            "high_price": "high",
            "low_price": "low",
            "close_price": "close",
        }
    )
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype(int)
    records = df.to_dict(orient="records")
    if not records:
        return 0

    upsert_sql = text(
        """
        INSERT INTO daily_ohlcv (symbol, date, open, high, low, close, volume)
        VALUES (:symbol, :date, :open, :high, :low, :close, :volume)
        ON DUPLICATE KEY UPDATE
            open = VALUES(open),
            high = VALUES(high),
            low = VALUES(low),
            close = VALUES(close),
            volume = VALUES(volume)
        """
    )
    with engine.begin() as conn:
        conn.execute(upsert_sql, records)
    log.info("Loaded %d daily OHLCV rows", len(records))
    return len(records)


def load_eod_rows(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    engine = get_engine()
    upsert_sql = text(
        """
        INSERT INTO daily_ohlcv (symbol, date, open, high, low, close, volume)
        VALUES (:symbol, :date, :open, :high, :low, :close, :volume)
        ON DUPLICATE KEY UPDATE
            open = VALUES(open),
            high = VALUES(high),
            low = VALUES(low),
            close = VALUES(close),
            volume = VALUES(volume)
        """
    )
    with engine.begin() as conn:
        conn.execute(upsert_sql, rows)
    log.info("Loaded %d aggregated EOD rows", len(rows))
    return len(rows)


def load_overview_cache(cfg: EtlConfig) -> int:
    engine = get_engine()
    records = []
    for symbol in cfg.symbols:
        payload = _read_json(_raw_json_path(cfg, "overview", symbol))
        if isinstance(payload, list) and payload:
            payload = payload[0]
        if isinstance(payload, dict):
            records.append({"symbol": symbol.upper(), "payload_json": _json_dumps(payload), "source": "etl-vnstock"})
    if not records:
        return 0
    sql = text(
        """
        INSERT INTO company_overview_cache (symbol, payload_json, source, updated_at)
        VALUES (:symbol, :payload_json, :source, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE payload_json=VALUES(payload_json), source=VALUES(source), updated_at=CURRENT_TIMESTAMP
        """
    )
    with engine.begin() as conn:
        conn.execute(sql, records)
    log.info("Loaded %d overview cache rows", len(records))
    return len(records)


def load_financial_cache(cfg: EtlConfig) -> int:
    engine = get_engine()
    records = []
    for symbol in cfg.symbols:
        for report_type in FUNDAMENTAL_REPORT_TYPES:
            payload = _read_json(_raw_json_path(cfg, f"fundamental/{report_type}", symbol))
            if isinstance(payload, list):
                records.append(
                    {
                        "symbol": symbol.upper(),
                        "report_type": report_type,
                        "row_count": len(payload),
                        "payload_json": _json_dumps(payload),
                        "source": f"etl-vnstock-{report_type}",
                    }
                )
    if not records:
        return 0
    sql = text(
        """
        INSERT INTO financial_report_cache (symbol, report_type, row_count, payload_json, source, updated_at)
        VALUES (:symbol, :report_type, :row_count, :payload_json, :source, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE
            row_count=VALUES(row_count),
            payload_json=VALUES(payload_json),
            source=VALUES(source),
            updated_at=CURRENT_TIMESTAMP
        """
    )
    with engine.begin() as conn:
        conn.execute(sql, records)
    log.info("Loaded %d financial cache rows", len(records))
    return len(records)


def _load_symbol_list_cache(cfg: EtlConfig, category: str, table_name: str, source: str) -> int:
    engine = get_engine()
    records = []
    for symbol in cfg.symbols:
        payload = _read_json(_raw_json_path(cfg, category, symbol))
        if isinstance(payload, list):
            records.append(
                {
                    "symbol": symbol.upper(),
                    "item_count": len(payload),
                    "payload_json": _json_dumps(payload),
                    "source": source,
                }
            )
    if not records:
        return 0
    sql = text(
        f"""
        INSERT INTO {table_name} (symbol, item_count, payload_json, source, updated_at)
        VALUES (:symbol, :item_count, :payload_json, :source, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE
            item_count=VALUES(item_count),
            payload_json=VALUES(payload_json),
            source=VALUES(source),
            updated_at=CURRENT_TIMESTAMP
        """
    )
    with engine.begin() as conn:
        conn.execute(sql, records)
    log.info("Loaded %d %s rows", len(records), table_name)
    return len(records)


def load_news_cache(cfg: EtlConfig) -> int:
    return _load_symbol_list_cache(cfg, "news", "news_cache", "etl-vnstock-news")


def load_events_cache(cfg: EtlConfig) -> int:
    return _load_symbol_list_cache(cfg, "events", "events_cache", "etl-vnstock-events")


def _series_values(df: pd.DataFrame, col: str) -> list[Any]:
    if col not in df.columns:
        return []
    values = df[col].where(pd.notna(df[col]), None).tolist()
    return values


def _float_series(values: pd.Series) -> list[float]:
    cleaned = pd.to_numeric(values, errors="coerce").fillna(0.0)
    return [float(round(item, 4)) for item in cleaned.tolist()]


def _latest_float(values: pd.Series, fallback: float = 0.0) -> float:
    if values.empty:
        return fallback
    parsed = pd.to_numeric(values.iloc[-1], errors="coerce")
    return fallback if pd.isna(parsed) else float(parsed)


def _technical_payload_from_processed(symbol: str, frame: pd.DataFrame) -> dict[str, Any]:
    frame = frame.sort_values("data_date").reset_index(drop=True)
    close = pd.to_numeric(frame["close_price"], errors="coerce").fillna(0.0)
    high = pd.to_numeric(frame["high_price"], errors="coerce").fillna(0.0)
    low = pd.to_numeric(frame["low_price"], errors="coerce").fillna(0.0)
    volume = pd.to_numeric(frame["volume"], errors="coerce").fillna(0.0)

    sma_20 = close.rolling(window=20, min_periods=1).mean()
    sma_50 = close.rolling(window=50, min_periods=1).mean()
    sma_200 = close.rolling(window=200, min_periods=1).mean()
    sma_7 = close.rolling(window=7, min_periods=1).mean()
    sma_21 = close.rolling(window=21, min_periods=1).mean()
    ema_12 = close.ewm(span=12, adjust=False, min_periods=1).mean()
    ema_26 = close.ewm(span=26, adjust=False, min_periods=1).mean()

    delta = close.diff().fillna(0.0)
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)
    avg_gain = gains.rolling(window=14, min_periods=14).mean()
    avg_loss = losses.rolling(window=14, min_periods=14).mean().replace(0, pd.NA)
    rsi = (100 - (100 / (1 + (avg_gain / avg_loss)))).fillna(50.0)

    macd_line = ema_12 - ema_26
    macd_signal = macd_line.ewm(span=9, adjust=False, min_periods=1).mean()
    macd_histogram = macd_line - macd_signal
    bb_middle = sma_20
    bb_std = close.rolling(window=20, min_periods=1).std().fillna(0.0)
    bb_upper = bb_middle + 2 * bb_std
    bb_lower = bb_middle - 2 * bb_std

    lowest_low = low.rolling(window=14, min_periods=1).min()
    highest_high = high.rolling(window=14, min_periods=1).max()
    stoch_range = (highest_high - lowest_low).replace(0, pd.NA)
    stoch_k = (((close - lowest_low) / stoch_range) * 100).fillna(50.0)
    stoch_d = stoch_k.rolling(window=3, min_periods=1).mean()

    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr_14 = tr.rolling(window=14, min_periods=1).mean().fillna(0.0)

    direction = pd.Series(0, index=close.index, dtype=float)
    direction[close > close.shift(1)] = 1.0
    direction[close < close.shift(1)] = -1.0
    obv = (direction * volume).cumsum()
    if not obv.empty:
        obv.iloc[0] = 0.0

    latest_rsi = _latest_float(rsi, fallback=50.0)
    rsi_signal = "oversold" if latest_rsi < 30 else "overbought" if latest_rsi > 70 else "neutral"
    macd_bias = "bullish" if _latest_float(macd_line) >= _latest_float(macd_signal) else "bearish"
    price_vs_sma200 = "above" if _latest_float(close) >= _latest_float(sma_200, fallback=_latest_float(close)) else "below"
    golden_cross = False
    if len(sma_50) > 1 and len(sma_200) > 1:
        previous = float(sma_50.iloc[-2]) >= float(sma_200.iloc[-2])
        current = float(sma_50.iloc[-1]) >= float(sma_200.iloc[-1])
        golden_cross = current and not previous

    score = 0
    score += 1 if rsi_signal == "oversold" else -1 if rsi_signal == "overbought" else 0
    score += 1 if macd_bias == "bullish" else -1
    score += 1 if price_vs_sma200 == "above" else -1
    score += 1 if golden_cross else 0
    summary = "strong_buy" if score >= 3 else "buy" if score == 2 else "strong_sell" if score <= -3 else "sell" if score <= -2 else "neutral"

    indicators = {
        "sma_7": _float_series(sma_7),
        "sma_21": _float_series(sma_21),
        "sma_20": _float_series(sma_20),
        "sma_50": _float_series(sma_50),
        "sma_200": _float_series(sma_200),
        "ema_12": _float_series(ema_12),
        "ema_26": _float_series(ema_26),
        "rsi_14": _float_series(rsi),
        "macd": _float_series(macd_line),
        "macd_line": _float_series(macd_line),
        "signal": _float_series(macd_signal),
        "macd_signal": _float_series(macd_signal),
        "macd_histogram": _float_series(macd_histogram),
        "bb_upper": _float_series(bb_upper),
        "bb_middle": _float_series(bb_middle),
        "bb_lower": _float_series(bb_lower),
        "stoch_k": _float_series(stoch_k),
        "stoch_d": _float_series(stoch_d),
        "atr_14": _float_series(atr_14),
        "obv": _float_series(obv),
    }
    return {
        "symbol": symbol,
        "count": int(len(frame)),
        "ohlcv": {
            "time": frame["data_date"].astype(str).tolist(),
            "open": _float_series(frame["open_price"]),
            "high": _float_series(frame["high_price"]),
            "low": _float_series(frame["low_price"]),
            "close": _float_series(frame["close_price"]),
            "volume": _float_series(frame["volume"]),
        },
        "indicators": indicators,
        "signals": {
            "rsi": rsi_signal,
            "macd": macd_bias,
            "golden_cross": bool(golden_cross),
            "price_vs_sma200": price_vs_sma200,
            "summary": summary,
        },
    }


def load_technical_cache(cfg: EtlConfig, dataset: pd.DataFrame | None = None, limit: int = 365) -> int:
    engine = get_engine()
    if dataset is None:
        latest_file = _latest_processed_parquet(cfg)
        if not latest_file:
            return 0
        dataset = pd.read_parquet(latest_file)

    records = []
    for symbol, frame in dataset.groupby("symbol"):
        frame = frame.sort_values("data_date").tail(limit)
        payload = _technical_payload_from_processed(str(symbol).upper(), frame)
        records.append(
            {
                "symbol": str(symbol).upper(),
                "start_date": None,
                "end_date": None,
                "limit_value": limit,
                "history_count": len(frame),
                "history_last_time": str(frame["data_date"].iloc[-1]) if not frame.empty else None,
                "payload_json": _json_dumps(payload),
                "source": "etl-processed",
            }
        )
    if not records:
        return 0
    delete_sql = text(
        """
        DELETE FROM technical_cache
        WHERE symbol = :symbol
          AND start_date IS NULL
          AND end_date IS NULL
          AND limit_value = :limit_value
        """
    )
    sql = text(
        """
        INSERT INTO technical_cache
            (symbol, start_date, end_date, limit_value, history_count, history_last_time, payload_json, source, updated_at)
        VALUES
            (:symbol, :start_date, :end_date, :limit_value, :history_count, :history_last_time, :payload_json, :source, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE
            history_count=VALUES(history_count),
            history_last_time=VALUES(history_last_time),
            payload_json=VALUES(payload_json),
            source=VALUES(source),
            updated_at=CURRENT_TIMESTAMP
        """
    )
    with engine.begin() as conn:
        conn.execute(delete_sql, [{"symbol": row["symbol"], "limit_value": row["limit_value"]} for row in records])
        conn.execute(sql, records)
    log.info("Loaded %d technical cache rows", len(records))
    return len(records)


def load_all(cfg: EtlConfig, dataset: pd.DataFrame | None = None) -> dict[str, int]:
    if dataset is None:
        latest_file = _latest_processed_parquet(cfg)
        dataset = pd.read_parquet(latest_file) if latest_file else None
    results = {
        "daily_ohlcv": load_daily_price(cfg, dataset),
        "overview": load_overview_cache(cfg),
        "financial": load_financial_cache(cfg),
        "news": load_news_cache(cfg),
        "events": load_events_cache(cfg),
        "technical": load_technical_cache(cfg, dataset),
    }
    log.info("MySQL load_all results: %s", results)
    return results


if __name__ == "__main__":
    load_daily_price()
