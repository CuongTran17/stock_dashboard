import asyncio
import httpx
import json
import logging
import math
import os
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from vnstock import Company, Finance, Quote

from src.database.db import AsyncSessionLocal, SessionLocal, init_db
from src.database.models import (
    AIPrediction,
    CompanyOverviewCache,
    EventsCache,
    FinancialReportCache,
    NewsCache,
    TechnicalCache,
)
from src.jobs import build_lifespan
from src.services.fundamental_fetcher import fundamental_service
from src.services.vnstock_fetcher import (
    VN_TZ,
    VN30_SYMBOLS,
    fetcher_service,
    is_vn30_symbol,
    normalize_symbol,
    parse_symbols_query,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _extract_kaggle_output_text(payload: Any) -> str:
    if not isinstance(payload, dict):
        if isinstance(payload, str):
            return payload.strip()
        return ""

    candidate_keys = (
        "raw_output",
        "raw_text",
        "output",
        "response",
        "content",
        "message",
        "text",
        "answer",
    )

    for key in candidate_keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for key in ("data", "result", "analysis", "payload"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            nested_text = _extract_kaggle_output_text(nested)
            if nested_text:
                return nested_text
        elif isinstance(nested, str) and nested.strip():
            return nested.strip()

    return json.dumps(payload, ensure_ascii=False)


def _extract_kaggle_key_factors(raw_text: str) -> list[str]:
    if not raw_text.strip():
        return []

    factors: list[str] = []

    bracket_match = re.search(r"KEY_FACTORS\s*:\s*\[(.*?)\]", raw_text, flags=re.IGNORECASE | re.DOTALL)
    if bracket_match:
        items = bracket_match.group(1)
        for chunk in re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", items):
            factor = chunk.strip().strip('"').strip("'").strip()
            if factor:
                factors.append(factor)

    if factors:
        return list(dict.fromkeys(factors))

    list_match = re.search(r"KEY_FACTORS\s*:\s*(.+)", raw_text, flags=re.IGNORECASE | re.DOTALL)
    if list_match:
        tail = list_match.group(1)
        tail = re.split(r"\n\s*(?:FINAL DECISION|CONFIDENCE|<\/think>|<\|think\|>)", tail, maxsplit=1, flags=re.IGNORECASE)[0]
        for line in tail.splitlines():
            candidate = line.strip()
            candidate = re.sub(r"^[\-\*\d\.\)\s]+", "", candidate)
            if candidate:
                factors.append(candidate)

    return list(dict.fromkeys(factors))

COMPANY_SOURCE = os.getenv("VNSTOCK_COMPANY_SOURCE", "kbs")
FINANCE_SOURCE = os.getenv("VNSTOCK_FINANCE_SOURCE", "vci")
NEWS_CACHE_TTL_SECONDS = max(int(os.getenv("VNSTOCK_NEWS_CACHE_TTL_SECONDS", "300")), 60)
EVENTS_CACHE_TTL_SECONDS = max(int(os.getenv("VNSTOCK_EVENTS_CACHE_TTL_SECONDS", "900")), 120)
OVERVIEW_CACHE_TTL_SECONDS = max(int(os.getenv("VNSTOCK_OVERVIEW_CACHE_TTL_SECONDS", "21600")), 300)
FINANCIAL_CACHE_TTL_SECONDS = max(int(os.getenv("VNSTOCK_FINANCIAL_CACHE_TTL_SECONDS", "21600")), 300)
TECHNICAL_CACHE_TTL_SECONDS = max(int(os.getenv("VNSTOCK_TECHNICAL_CACHE_TTL_SECONDS", "900")), 60)
MAX_NEWS_PER_SYMBOL = max(int(os.getenv("VNSTOCK_NEWS_PER_SYMBOL", "20")), 5)
MAX_EVENTS_PER_SYMBOL = max(int(os.getenv("VNSTOCK_EVENTS_PER_SYMBOL", "12")), 5)
MAX_FINANCIAL_ROWS = max(int(os.getenv("VNSTOCK_FINANCIAL_MAX_ROWS", "120")), 10)
PRELOAD_REFERENCE_CACHE_ENABLED = _env_flag("VNSTOCK_PRELOAD_REFERENCE_CACHE", True)
PRELOAD_REFERENCE_FORCE_REFRESH = _env_flag("VNSTOCK_PRELOAD_FORCE_REFRESH", False)
PRELOAD_REFERENCE_SYMBOL_LIMIT = max(1, min(len(VN30_SYMBOLS), _env_int("VNSTOCK_PRELOAD_SYMBOL_LIMIT", 5)))

FINANCIAL_METHODS: dict[str, str] = {
    "income": "income_statement",
    "balance": "balance_sheet",
    "cashflow": "cash_flow",
    "ratios": "ratio",
}

MARKET_INDEX_HISTORY_TTL_SECONDS = max(int(os.getenv("VNSTOCK_MARKET_INDEX_CACHE_TTL_SECONDS", "180")), 30)
MARKET_INDEX_LOOKBACK_DAYS = max(int(os.getenv("VNSTOCK_MARKET_INDEX_LOOKBACK_DAYS", "540")), 120)
INTRADAY_STALE_SECONDS = max(int(os.getenv("VNSTOCK_INTRADAY_STALE_SECONDS", "20")), 3)
INTRADAY_REFRESH_TIMEOUT_SECONDS = max(float(os.getenv("VNSTOCK_INTRADAY_REFRESH_TIMEOUT_SECONDS", "4.0")), 1.0)

MARKET_INDEX_DEFINITIONS: dict[str, dict[str, str]] = {
    "VNINDEX": {"name": "VN-Index", "vnstock_symbol": "VNINDEX"},
    "VN30": {"name": "VN30", "vnstock_symbol": "VN30"},
    "HNX": {"name": "HNX-Index", "vnstock_symbol": "HNXINDEX"},
    "UPCOM": {"name": "UPCoM", "vnstock_symbol": "UPCOMINDEX"},
}
MARKET_INDEX_ORDER = ["VNINDEX", "VN30", "HNX", "UPCOM"]
MARKET_INDEX_ALIASES: dict[str, str] = {
    "VNINDEX": "VNINDEX",
    "VN-INDEX": "VNINDEX",
    "VN30": "VN30",
    "HNX": "HNX",
    "HNXINDEX": "HNX",
    "HNX-INDEX": "HNX",
    "UPCOM": "UPCOM",
    "UPCOMINDEX": "UPCOM",
    "UPCOM-INDEX": "UPCOM",
}

_news_cache: dict[str, dict[str, Any]] = {}
_events_cache: dict[str, dict[str, Any]] = {}
_market_index_history_cache: dict[str, dict[str, Any]] = {}
_news_lock = asyncio.Lock()
_events_lock = asyncio.Lock()
_market_index_lock = asyncio.Lock()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        parsed = value.to_pydatetime()
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)

    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds > 1_000_000_000_000:
            seconds /= 1000.0
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None

        if raw.isdigit():
            return _parse_datetime(int(raw))

        for candidate in (raw, raw.replace("Z", "+00:00"), raw.replace(" ", "T")):
            try:
                parsed = datetime.fromisoformat(candidate)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                continue

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                parsed = datetime.strptime(raw, fmt)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    return None


def _to_iso_datetime(value: Any, fallback: Optional[str] = None) -> str:
    parsed = _parse_datetime(value)
    if parsed:
        return parsed.isoformat()
    if fallback:
        return fallback
    return _utc_now().isoformat()


def _to_iso_date(value: Any) -> str:
    parsed = _parse_datetime(value)
    if parsed:
        return parsed.date().isoformat()
    return ""


def _intraday_cache_age_seconds() -> Optional[float]:
    last_sync = _parse_datetime(fetcher_service.last_intraday_sync_at)
    if last_sync is None:
        return None
    return max((_utc_now() - last_sync).total_seconds(), 0.0)


def _intraday_cache_is_stale(max_age_seconds: int = INTRADAY_STALE_SECONDS) -> bool:
    age_seconds = _intraday_cache_age_seconds()
    if age_seconds is None:
        return True
    return age_seconds > float(max(max_age_seconds, 1))


async def _safe_refresh_symbols_once(symbols: list[str], ignore_session: bool = False) -> int:
    try:
        return await asyncio.wait_for(
            fetcher_service.refresh_symbols_once(symbols, ignore_session=ignore_session),
            timeout=INTRADAY_REFRESH_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "Timed out refreshing symbols after %.1fs (symbols=%s)",
            INTRADAY_REFRESH_TIMEOUT_SECONDS,
            ",".join(symbols[:6]),
        )
        return 0
    except Exception as exc:
        logger.warning("Failed guarded refresh for symbols %s: %s", symbols[:6], exc)
        return 0


async def _safe_refresh_symbol(symbol: str, ignore_session: bool = False) -> bool:
    try:
        return await asyncio.wait_for(
            fetcher_service.refresh_symbol_intraday(symbol, ignore_session=ignore_session),
            timeout=INTRADAY_REFRESH_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "Timed out refreshing symbol %s after %.1fs",
            symbol,
            INTRADAY_REFRESH_TIMEOUT_SECONDS,
        )
        return False
    except Exception as exc:
        logger.warning("Failed guarded refresh for symbol %s: %s", symbol, exc)
        return False


def _build_intraday_bars_from_ticks(
    ticks: list[dict[str, Any]],
    interval_minutes: int = 1,
) -> list[dict[str, Any]]:
    safe_interval = max(interval_minutes, 1)
    bucket_seconds = safe_interval * 60

    buckets: dict[int, dict[str, Any]] = {}
    ordered_ticks = sorted(ticks, key=lambda item: str(item.get("time") or ""))
    for tick in ordered_ticks:
        price = _to_float(tick.get("price"))
        if price <= 0:
            continue

        parsed_time = _parse_datetime(tick.get("time"))
        if parsed_time is None:
            continue

        local_time = parsed_time.astimezone(VN_TZ)
        bucket_epoch = int(local_time.timestamp()) // bucket_seconds * bucket_seconds
        volume = _to_int(tick.get("volume"))

        candle = buckets.get(bucket_epoch)
        if candle is None:
            bucket_time = datetime.fromtimestamp(bucket_epoch, tz=VN_TZ).replace(second=0, microsecond=0)
            buckets[bucket_epoch] = {
                "time": bucket_time.isoformat(),
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume,
            }
            continue

        candle["high"] = max(_to_float(candle.get("high")), price)
        candle["low"] = min(_to_float(candle.get("low"), fallback=price), price)
        candle["close"] = price
        candle["volume"] = _to_int(candle.get("volume")) + volume

    return [buckets[key] for key in sorted(buckets.keys())]


def _impact_from_price_change_pct(value: Any) -> str:
    pct = _to_float(value, fallback=0.0)
    if abs(pct) <= 1:
        pct *= 100.0

    abs_pct = abs(pct)
    if abs_pct >= 3.0:
        return "high"
    if abs_pct >= 1.0:
        return "medium"
    return "low"


def _cache_fresh(entry: Optional[dict[str, Any]], ttl_seconds: int) -> bool:
    if not entry:
        return False
    updated_at = entry.get("updated_at")
    if not isinstance(updated_at, datetime):
        return False
    return (_utc_now() - updated_at).total_seconds() < ttl_seconds


def _normalize_column_name(column: Any) -> str:
    if isinstance(column, tuple):
        parts = [str(part).strip() for part in column if str(part).strip()]
        return " | ".join(parts)
    return str(column).strip()


def _normalize_scalar(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().isoformat()

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return int(value)

    if isinstance(value, float):
        return float(value) if math.isfinite(value) else None

    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None

    if isinstance(value, dict):
        return {str(key): _normalize_scalar(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_normalize_scalar(item) for item in value]

    if hasattr(value, "item"):
        try:
            return _normalize_scalar(value.item())
        except Exception:
            pass

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return str(value)


def _frame_to_records(frame: Optional[pd.DataFrame]) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []

    rows: list[dict[str, Any]] = []
    for row in frame.to_dict("records"):
        normalized_row: dict[str, Any] = {}
        for key, value in row.items():
            normalized_key = _normalize_column_name(key)
            if normalized_key:
                normalized_row[normalized_key] = _normalize_scalar(value)
        if normalized_row:
            rows.append(normalized_row)
    return rows


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(payload_json: str, fallback: Any) -> Any:
    try:
        return json.loads(payload_json)
    except Exception:
        return fallback


def _row_iso_timestamp(value: Any) -> Optional[str]:
    parsed = _parse_datetime(value)
    return parsed.isoformat() if parsed else None


def _row_is_fresh(updated_at: Any, ttl_seconds: int) -> bool:
    parsed = _parse_datetime(updated_at)
    if not parsed:
        return False
    return (_utc_now() - parsed).total_seconds() < ttl_seconds


async def _load_symbol_payload_cache(model_cls: Any, symbol: str, max_age_seconds: Optional[int]) -> tuple[Optional[Any], Optional[str]]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(model_cls).where(model_cls.symbol == symbol))
        row = result.scalars().first()
        if not row:
            return None, None

        if max_age_seconds is not None and not _row_is_fresh(row.updated_at, max_age_seconds):
            return None, _row_iso_timestamp(row.updated_at)

        payload = _json_loads(row.payload_json, fallback=[])
        return payload, _row_iso_timestamp(row.updated_at)


async def _save_symbol_payload_cache(model_cls: Any, symbol: str, payload: Any, source: str) -> Optional[str]:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(model_cls).where(model_cls.symbol == symbol))
            row = result.scalars().first()
            if row is None:
                row = model_cls(symbol=symbol)

            row.payload_json = _json_dumps(payload)
            if hasattr(row, "item_count"):
                row.item_count = len(payload) if isinstance(payload, list) else 0
            if hasattr(row, "source"):
                row.source = source
            row.updated_at = datetime.utcnow()

            db.add(row)
            await db.commit()
            return _row_iso_timestamp(row.updated_at)
        except Exception as exc:
            await db.rollback()
            logger.warning("Failed to save %s cache for %s: %s", model_cls.__name__, symbol, exc)
            return None


async def _load_financial_report_cache(
    symbol: str,
    report_type: str,
    max_age_seconds: Optional[int],
) -> tuple[Optional[list[dict[str, Any]]], Optional[str]]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FinancialReportCache).where(
                FinancialReportCache.symbol == symbol,
                FinancialReportCache.report_type == report_type,
            )
        )
        row = result.scalars().first()
        if not row:
            return None, None

        if max_age_seconds is not None and not _row_is_fresh(row.updated_at, max_age_seconds):
            return None, _row_iso_timestamp(row.updated_at)

        payload = _json_loads(row.payload_json, fallback=[])
        if not isinstance(payload, list):
            payload = []
        return payload, _row_iso_timestamp(row.updated_at)


async def _save_financial_report_cache(
    symbol: str,
    report_type: str,
    records: list[dict[str, Any]],
    source: str,
) -> Optional[str]:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(FinancialReportCache).where(
                    FinancialReportCache.symbol == symbol,
                    FinancialReportCache.report_type == report_type,
                )
            )
            row = result.scalars().first()
            if row is None:
                row = FinancialReportCache(symbol=symbol, report_type=report_type)

            row.row_count = len(records)
            row.payload_json = _json_dumps(records)
            row.source = source
            row.updated_at = datetime.utcnow()

            db.add(row)
            await db.commit()
            return _row_iso_timestamp(row.updated_at)
        except Exception as exc:
            await db.rollback()
            logger.warning("Failed to save financial cache for %s (%s): %s", symbol, report_type, exc)
            return None


def _fetch_company_overview_sync(symbol: str) -> dict[str, Any]:
    company = Company(source=COMPANY_SOURCE, symbol=symbol)
    records = _frame_to_records(company.overview())
    if not records:
        return {}
    return records[0]


def _fetch_financial_report_sync(symbol: str, report_type: str) -> list[dict[str, Any]]:
    method_name = FINANCIAL_METHODS.get(report_type)
    if not method_name:
        return []

    finance = Finance(source=COMPANY_SOURCE, symbol=symbol)
    fetch_method = getattr(finance, method_name)
    records = _frame_to_records(fetch_method())
    return records[:MAX_FINANCIAL_ROWS]


async def _refresh_company_overview(symbol: str) -> tuple[dict[str, Any], Optional[str]]:
    await fetcher_service.wait_for_rate_slot()
    try:
        payload = await asyncio.to_thread(_fetch_company_overview_sync, symbol)
        synced_at = await _save_symbol_payload_cache(CompanyOverviewCache, symbol, payload, source="vnstock-company-overview")
        return payload, synced_at
    except BaseException as exc:
        logger.warning("Failed to fetch company overview for %s: %s", symbol, exc)
        payload, synced_at = await _load_symbol_payload_cache(CompanyOverviewCache, symbol, max_age_seconds=None)
        return payload or {}, synced_at


async def _refresh_financial_report(symbol: str, report_type: str) -> tuple[list[dict[str, Any]], Optional[str]]:
    await fetcher_service.wait_for_rate_slot()
    try:
        records = await asyncio.to_thread(_fetch_financial_report_sync, symbol, report_type)
        synced_at = await _save_financial_report_cache(symbol, report_type, records, source=f"vnstock-finance-{report_type}")
        return records, synced_at
    except BaseException as exc:
        logger.warning("Failed to fetch financial report for %s (%s): %s", symbol, report_type, exc)
        records, synced_at = await _load_financial_report_cache(symbol, report_type, max_age_seconds=None)
        return records or [], synced_at


def _to_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def _to_number_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
        return numeric if math.isfinite(numeric) else None
    if isinstance(value, str):
        raw = value.strip().replace(",", "")
        if not raw:
            return None
        try:
            numeric = float(raw)
            return numeric if math.isfinite(numeric) else None
        except ValueError:
            return None
    return None


def _select_latest_financial_record(records: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not records:
        return None

    def _row_sort_key(row: dict[str, Any]) -> tuple[int, int]:
        return (
            _to_int(row.get("yearReport") or row.get("year") or row.get("Year")),
            _to_int(row.get("lengthReport") or row.get("quarter") or row.get("Quarter")),
        )

    return max(records, key=_row_sort_key)


def _extract_metric(row: dict[str, Any], keywords: list[str]) -> Optional[float]:
    normalized_keywords = [item.lower() for item in keywords]
    for key, value in row.items():
        key_text = str(key).lower()
        if any(token in key_text for token in normalized_keywords):
            numeric = _to_number_or_none(value)
            if numeric is not None:
                return numeric
    return None


def _extract_valuation_from_ratios(records: list[dict[str, Any]]) -> dict[str, Optional[float]]:
    row = _select_latest_financial_record(records)
    if not row:
        return {
            "pe": None,
            "pb": None,
            "eps": None,
            "roe": None,
            "roa": None,
            "market_cap": None,
        }

    return {
        "pe": _extract_metric(row, ["p/e", " pe"]),
        "pb": _extract_metric(row, ["p/b", " pb"]),
        "eps": _extract_metric(row, ["eps"]),
        "roe": _extract_metric(row, ["roe"]),
        "roa": _extract_metric(row, ["roa"]),
        "market_cap": _extract_metric(row, ["market capital", "market cap"]),
    }


async def _load_technical_cache(
    symbol: str,
    start_date: Optional[date],
    end_date: Optional[date],
    limit: int,
) -> tuple[Optional[TechnicalCache], Optional[dict[str, Any]]]:
    async with AsyncSessionLocal() as db:
        query = select(TechnicalCache).where(
            TechnicalCache.symbol == symbol,
            TechnicalCache.limit_value == limit,
        )

        if start_date is None:
            query = query.where(TechnicalCache.start_date.is_(None))
        else:
            query = query.where(TechnicalCache.start_date == start_date)

        if end_date is None:
            query = query.where(TechnicalCache.end_date.is_(None))
        else:
            query = query.where(TechnicalCache.end_date == end_date)

        result = await db.execute(query)
        row = result.scalars().first()
        if not row:
            return None, None

        payload = _json_loads(row.payload_json, fallback={})
        if not isinstance(payload, dict):
            payload = {}
        return row, payload


async def _save_technical_cache(
    symbol: str,
    start_date: Optional[date],
    end_date: Optional[date],
    limit: int,
    history_count: int,
    history_last_time: Optional[str],
    payload: dict[str, Any],
) -> Optional[str]:
    async with AsyncSessionLocal() as db:
        try:
            query = select(TechnicalCache).where(
                TechnicalCache.symbol == symbol,
                TechnicalCache.limit_value == limit,
            )

            if start_date is None:
                query = query.where(TechnicalCache.start_date.is_(None))
            else:
                query = query.where(TechnicalCache.start_date == start_date)

            if end_date is None:
                query = query.where(TechnicalCache.end_date.is_(None))
            else:
                query = query.where(TechnicalCache.end_date == end_date)

            result = await db.execute(query)
            row = result.scalars().first()
            if row is None:
                row = TechnicalCache(symbol=symbol, start_date=start_date, end_date=end_date, limit_value=limit)

            row.history_count = history_count
            row.history_last_time = history_last_time
            row.payload_json = _json_dumps(payload)
            row.source = "mysql"
            row.updated_at = datetime.utcnow()

            db.add(row)
            await db.commit()
            return _row_iso_timestamp(row.updated_at)
        except Exception as exc:
            await db.rollback()
            logger.warning("Failed to save technical cache for %s: %s", symbol, exc)
            return None


def _fetch_symbol_news_sync(symbol: str) -> list[dict[str, Any]]:
    company = Company(source=COMPANY_SOURCE, symbol=symbol)
    frame = company.news()
    if frame is None or frame.empty:
        return []

    news_rows: list[dict[str, Any]] = []
    for row in frame.to_dict("records"):
        title = str(row.get("news_title") or row.get("friendly_sub_title") or "").strip()
        if not title:
            continue

        short_content = str(row.get("news_short_content") or row.get("news_sub_title") or title).strip()
        item_id = str(row.get("news_id") or row.get("id") or "").strip() or f"{symbol}-{len(news_rows) + 1}"
        published_iso = _to_iso_datetime(
            row.get("public_date") or row.get("created_at") or row.get("updated_at"),
            fallback=_utc_now().isoformat(),
        )

        news_rows.append(
            {
                "id": f"{symbol}-{item_id}",
                "symbol": symbol,
                "symbols": [symbol],
                "source": "vnstock",
                "title": title,
                "summary": short_content,
                "publish_time": published_iso,
                "time": published_iso,
                "url": str(row.get("news_source_link") or "").strip(),
                "impact": _impact_from_price_change_pct(row.get("price_change_pct")),
            }
        )

    news_rows.sort(key=lambda item: item.get("publish_time") or "", reverse=True)
    return news_rows[:MAX_NEWS_PER_SYMBOL]


def _fetch_symbol_events_sync(symbol: str) -> list[dict[str, Any]]:
    company = Company(source=COMPANY_SOURCE, symbol=symbol)
    frame = company.events()
    if frame is None or frame.empty:
        return []

    events_rows: list[dict[str, Any]] = []
    for row in frame.to_dict("records"):
        title = str(row.get("event_title") or row.get("event_list_name") or "").strip()
        if not title:
            continue

        raw_date = row.get("public_date") or row.get("issue_date") or row.get("record_date") or row.get("exright_date")
        date_value = _to_iso_date(raw_date)
        if not date_value or date_value == "1753-01-01":
            continue

        event_type = str(row.get("event_list_name") or "").strip()
        ratio = _to_float(row.get("ratio"), fallback=0.0)
        amount = _to_float(row.get("value"), fallback=0.0)
        details: list[str] = []
        if event_type:
            details.append(event_type)
        if ratio > 0:
            details.append(f"ratio {ratio:g}")
        if amount > 0:
            details.append(f"value {amount:g}")
        description = " | ".join(details) if details else "Corporate event update"

        item_id = str(row.get("id") or "").strip() or f"{symbol}-event-{len(events_rows) + 1}"
        events_rows.append(
            {
                "id": f"{symbol}-{item_id}",
                "symbol": symbol,
                "date": date_value,
                "title": title,
                "description": description,
            }
        )

    events_rows.sort(key=lambda item: item.get("date") or "", reverse=True)
    return events_rows[:MAX_EVENTS_PER_SYMBOL]


async def _get_symbol_news(symbol: str, refresh: bool) -> tuple[list[dict[str, Any]], Optional[str]]:
    normalized = normalize_symbol(symbol)
    async with _news_lock:
        entry = _news_cache.get(normalized)
        if not refresh and _cache_fresh(entry, NEWS_CACHE_TTL_SECONDS):
            return list(entry.get("items", [])), entry.get("updated_at", _utc_now()).isoformat()

    if not refresh:
        cached_items, cached_synced_at = await _load_symbol_payload_cache(
            NewsCache,
            normalized,
            max_age_seconds=None,
        )
        if isinstance(cached_items, list):
            parsed_synced_at = _parse_datetime(cached_synced_at) or _utc_now()
            async with _news_lock:
                _news_cache[normalized] = {"updated_at": parsed_synced_at, "items": list(cached_items)}
            return list(cached_items), cached_synced_at

    await fetcher_service.wait_for_rate_slot()
    try:
        items = await asyncio.to_thread(_fetch_symbol_news_sync, normalized)
        synced_at = _utc_now()
        async with _news_lock:
            _news_cache[normalized] = {"updated_at": synced_at, "items": items}
        persisted_synced_at = await _save_symbol_payload_cache(
            NewsCache,
            normalized,
            items,
            source="vnstock-company-news",
        )
        return list(items), persisted_synced_at or synced_at.isoformat()
    except BaseException as exc:
        logger.warning("Failed to fetch news for %s: %s", normalized, exc)
        async with _news_lock:
            entry = _news_cache.get(normalized)
            if entry:
                return list(entry.get("items", [])), entry.get("updated_at", _utc_now()).isoformat()

        fallback_items, fallback_synced_at = await _load_symbol_payload_cache(
            NewsCache,
            normalized,
            max_age_seconds=None,
        )
        if isinstance(fallback_items, list):
            return list(fallback_items), fallback_synced_at
        return [], None


async def _get_symbol_events(symbol: str, refresh: bool) -> tuple[list[dict[str, Any]], Optional[str]]:
    normalized = normalize_symbol(symbol)
    async with _events_lock:
        entry = _events_cache.get(normalized)
        if not refresh and _cache_fresh(entry, EVENTS_CACHE_TTL_SECONDS):
            return list(entry.get("items", [])), entry.get("updated_at", _utc_now()).isoformat()

    if not refresh:
        cached_items, cached_synced_at = await _load_symbol_payload_cache(
            EventsCache,
            normalized,
            max_age_seconds=None,
        )
        if isinstance(cached_items, list):
            parsed_synced_at = _parse_datetime(cached_synced_at) or _utc_now()
            async with _events_lock:
                _events_cache[normalized] = {"updated_at": parsed_synced_at, "items": list(cached_items)}
            return list(cached_items), cached_synced_at

    await fetcher_service.wait_for_rate_slot()
    try:
        items = await asyncio.to_thread(_fetch_symbol_events_sync, normalized)
        synced_at = _utc_now()
        async with _events_lock:
            _events_cache[normalized] = {"updated_at": synced_at, "items": items}
        persisted_synced_at = await _save_symbol_payload_cache(
            EventsCache,
            normalized,
            items,
            source="vnstock-company-events",
        )
        return list(items), persisted_synced_at or synced_at.isoformat()
    except BaseException as exc:
        logger.warning("Failed to fetch events for %s: %s", normalized, exc)
        async with _events_lock:
            entry = _events_cache.get(normalized)
            if entry:
                return list(entry.get("items", [])), entry.get("updated_at", _utc_now()).isoformat()

        fallback_items, fallback_synced_at = await _load_symbol_payload_cache(
            EventsCache,
            normalized,
            max_age_seconds=None,
        )
        if isinstance(fallback_items, list):
            return list(fallback_items), fallback_synced_at
        return [], None


def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _to_float_series(values: pd.Series) -> list[float]:
    cleaned = pd.to_numeric(values, errors="coerce").fillna(0.0)
    return [float(round(item, 4)) for item in cleaned.tolist()]


def _calculate_technical_payload(symbol: str, history: list[dict[str, Any]]) -> dict[str, Any]:
    frame = pd.DataFrame(history)
    if frame.empty:
        return {
            "symbol": symbol,
            "count": 0,
            "ohlcv": {"time": [], "open": [], "high": [], "low": [], "close": [], "volume": []},
            "indicators": {
                "sma_20": [], "sma_50": [], "sma_200": [],
                "ema_12": [], "ema_26": [], "rsi_14": [],
                "macd_line": [], "macd_signal": [], "macd_histogram": [],
                "bb_upper": [], "bb_middle": [], "bb_lower": [],
                "stoch_k": [], "stoch_d": [], "atr_14": [], "obv": [],
            },
            "signals": {
                "rsi": "neutral",
                "macd": "bearish",
                "golden_cross": False,
                "price_vs_sma200": "below",
                "summary": "neutral",
            },
        }

    time_values = frame["time"].astype(str).tolist()
    close = pd.to_numeric(frame["close"], errors="coerce").fillna(0.0)
    high = pd.to_numeric(frame["high"], errors="coerce").fillna(0.0)
    low = pd.to_numeric(frame["low"], errors="coerce").fillna(0.0)
    volume = pd.to_numeric(frame["volume"], errors="coerce").fillna(0.0)

    sma_20 = close.rolling(window=20, min_periods=1).mean()
    sma_50 = close.rolling(window=50, min_periods=1).mean()
    sma_200 = close.rolling(window=200, min_periods=1).mean()

    ema_12 = close.ewm(span=12, adjust=False, min_periods=1).mean()
    ema_26 = close.ewm(span=26, adjust=False, min_periods=1).mean()

    delta = close.diff().fillna(0.0)
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)
    avg_gain = gains.rolling(window=14, min_periods=14).mean()
    avg_loss = losses.rolling(window=14, min_periods=14).mean().replace(0, pd.NA)
    rs = avg_gain / avg_loss
    rsi = (100 - (100 / (1 + rs))).fillna(50.0)

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
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr_14 = tr.rolling(window=14, min_periods=1).mean().fillna(0.0)

    obv_values = [0.0]
    for idx in range(1, len(close)):
        if close.iloc[idx] > close.iloc[idx - 1]:
            obv_values.append(obv_values[-1] + float(volume.iloc[idx]))
        elif close.iloc[idx] < close.iloc[idx - 1]:
            obv_values.append(obv_values[-1] - float(volume.iloc[idx]))
        else:
            obv_values.append(obv_values[-1])
    obv = pd.Series(obv_values, index=close.index)

    latest_rsi = _to_float(rsi.iloc[-1], fallback=50.0)
    rsi_signal = "oversold" if latest_rsi < 30 else "overbought" if latest_rsi > 70 else "neutral"

    latest_macd = _to_float(macd_line.iloc[-1])
    latest_macd_signal = _to_float(macd_signal.iloc[-1])
    macd_bias = "bullish" if latest_macd >= latest_macd_signal else "bearish"

    latest_close = _to_float(close.iloc[-1])
    latest_sma200 = _to_float(sma_200.iloc[-1], fallback=latest_close)
    price_vs_sma200 = "above" if latest_close >= latest_sma200 else "below"

    previous_cross_state = False
    if len(sma_50) > 1 and len(sma_200) > 1:
        previous_cross_state = _to_float(sma_50.iloc[-2]) >= _to_float(sma_200.iloc[-2])
    current_cross_state = _to_float(sma_50.iloc[-1]) >= _to_float(sma_200.iloc[-1])
    golden_cross = current_cross_state and not previous_cross_state

    score = 0
    if rsi_signal == "oversold":
        score += 1
    elif rsi_signal == "overbought":
        score -= 1
    score += 1 if macd_bias == "bullish" else -1
    score += 1 if price_vs_sma200 == "above" else -1
    if golden_cross:
        score += 1

    if score >= 3:
        summary = "strong_buy"
    elif score == 2:
        summary = "buy"
    elif score <= -3:
        summary = "strong_sell"
    elif score <= -2:
        summary = "sell"
    else:
        summary = "neutral"

    return {
        "symbol": symbol,
        "count": len(frame),
        "ohlcv": {
            "time": time_values,
            "open": _to_float_series(frame["open"]),
            "high": _to_float_series(frame["high"]),
            "low": _to_float_series(frame["low"]),
            "close": _to_float_series(frame["close"]),
            "volume": _to_float_series(frame["volume"]),
        },
        "indicators": {
            "sma_20": _to_float_series(sma_20),
            "sma_50": _to_float_series(sma_50),
            "sma_200": _to_float_series(sma_200),
            "ema_12": _to_float_series(ema_12),
            "ema_26": _to_float_series(ema_26),
            "rsi_14": _to_float_series(rsi),
            "macd_line": _to_float_series(macd_line),
            "macd_signal": _to_float_series(macd_signal),
            "macd_histogram": _to_float_series(macd_histogram),
            "bb_upper": _to_float_series(bb_upper),
            "bb_middle": _to_float_series(bb_middle),
            "bb_lower": _to_float_series(bb_lower),
            "stoch_k": _to_float_series(stoch_k),
            "stoch_d": _to_float_series(stoch_d),
            "atr_14": _to_float_series(atr_14),
            "obv": _to_float_series(obv),
        },
        "signals": {
            "rsi": rsi_signal,
            "macd": macd_bias,
            "golden_cross": bool(golden_cross),
            "price_vs_sma200": price_vs_sma200,
            "summary": summary,
        },
    }


def aggregate_eod_data() -> None:
    try:
        affected = fetcher_service.aggregate_today_intraday_to_daily()
        logger.info("EOD aggregation completed. affected_symbols=%s", affected)
    except Exception as exc:
        logger.error("EOD aggregation failed: %s", exc)


def _cache_has_content(payload: Any) -> bool:
    if payload is None:
        return False
    if isinstance(payload, dict):
        return len(payload) > 0
    if isinstance(payload, list):
        return len(payload) > 0
    return True


def _normalize_market_index_symbol(symbol: str) -> str:
    normalized = (symbol or "").strip().upper().replace(" ", "")
    canonical = MARKET_INDEX_ALIASES.get(normalized)
    if canonical:
        return canonical

    raise HTTPException(
        status_code=404,
        detail=f"Unsupported market index '{symbol}'. Supported values: VNINDEX, VN30, HNX, UPCOM.",
    )


def _market_index_history_cache_key(
    index_symbol: str,
    start_date: Optional[date],
    end_date: Optional[date],
    limit: int,
) -> str:
    start_value = start_date.isoformat() if start_date else ""
    end_value = end_date.isoformat() if end_date else ""
    return f"{index_symbol}|{start_value}|{end_value}|{limit}"


def _fetch_market_index_history_sync(vnstock_symbol: str, start: str, end: str) -> list[dict[str, Any]]:
    quote = Quote(source=fetcher_service.quote_source, symbol=vnstock_symbol)
    frame = quote.history(start=start, end=end, interval="1D")
    if frame is None or frame.empty:
        return []

    rows: list[dict[str, Any]] = []
    for raw in frame.to_dict("records"):
        row_date = _to_iso_date(raw.get("time") or raw.get("date"))
        if not row_date:
            continue

        rows.append(
            {
                "time": row_date,
                "open": _to_float(raw.get("open")),
                "high": _to_float(raw.get("high")),
                "low": _to_float(raw.get("low")),
                "close": _to_float(raw.get("close")),
                "volume": _to_int(raw.get("volume")),
            }
        )

    rows.sort(key=lambda item: str(item.get("time") or ""))
    return rows


async def _get_market_index_history_rows(
    index_symbol: str,
    start_date: Optional[date],
    end_date: Optional[date],
    limit: int,
    refresh: bool,
) -> tuple[list[dict[str, Any]], Optional[str], str]:
    safe_limit = max(2, min(limit, 5000))
    safe_end_date = end_date or _utc_now().date()
    safe_start_date = start_date or (safe_end_date - timedelta(days=max(safe_limit * 2, MARKET_INDEX_LOOKBACK_DAYS)))
    if safe_start_date > safe_end_date:
        safe_start_date, safe_end_date = safe_end_date, safe_start_date

    cache_key = _market_index_history_cache_key(index_symbol, safe_start_date, safe_end_date, safe_limit)
    if not refresh:
        async with _market_index_lock:
            entry = _market_index_history_cache.get(cache_key)
            if _cache_fresh(entry, MARKET_INDEX_HISTORY_TTL_SECONDS):
                return list(entry.get("rows", [])), entry.get("synced_at"), "memory-market-index-cache"

    await fetcher_service.wait_for_rate_slot()
    definition = MARKET_INDEX_DEFINITIONS[index_symbol]
    try:
        rows = await asyncio.to_thread(
            _fetch_market_index_history_sync,
            definition["vnstock_symbol"],
            safe_start_date.isoformat(),
            safe_end_date.isoformat(),
        )
        clipped_rows = rows[-safe_limit:]
        synced_at = _utc_now().isoformat()

        async with _market_index_lock:
            _market_index_history_cache[cache_key] = {
                "updated_at": _utc_now(),
                "rows": list(clipped_rows),
                "synced_at": synced_at,
            }

        return list(clipped_rows), synced_at, f"vnstock-{definition['vnstock_symbol'].lower()}"
    except BaseException as exc:
        logger.warning("Failed to fetch market index history for %s: %s", index_symbol, exc)

    async with _market_index_lock:
        stale = _market_index_history_cache.get(cache_key)
        if stale:
            return list(stale.get("rows", [])), stale.get("synced_at"), "memory-market-index-cache-stale"

    return [], None, "vnstock-market-index-unavailable"


def _build_market_index_quote(index_symbol: str, history_rows: list[dict[str, Any]]) -> dict[str, Any]:
    definition = MARKET_INDEX_DEFINITIONS[index_symbol]
    if not history_rows:
        return {
            "symbol": index_symbol,
            "name": definition["name"],
            "price": 0.0,
            "change": 0.0,
            "changePercent": 0.0,
            "volume": 0,
            "time": _utc_now().isoformat(),
        }

    latest = history_rows[-1]
    previous = history_rows[-2] if len(history_rows) > 1 else latest

    latest_close = _to_float(latest.get("close"))
    previous_close = _to_float(previous.get("close"), fallback=latest_close)
    change = latest_close - previous_close
    change_percent = (change / previous_close * 100.0) if previous_close > 0 else 0.0

    return {
        "symbol": index_symbol,
        "name": definition["name"],
        "price": round(latest_close, 2),
        "change": round(change, 2),
        "changePercent": round(change_percent, 2),
        "volume": _to_int(latest.get("volume")),
        "time": str(latest.get("time") or _utc_now().isoformat()),
    }


async def _preload_symbol_reference_cache(symbol: str, force_refresh: bool) -> None:
    normalized = normalize_symbol(symbol)

    cached_overview: Any = None
    if not force_refresh:
        cached_overview, _ = await _load_symbol_payload_cache(CompanyOverviewCache, normalized, max_age_seconds=None)
    if force_refresh or not _cache_has_content(cached_overview):
        await _refresh_company_overview(normalized)

    for report_type in FINANCIAL_METHODS:
        cached_rows: Any = None
        if not force_refresh:
            cached_rows, _ = await _load_financial_report_cache(normalized, report_type, max_age_seconds=None)
        if force_refresh or not _cache_has_content(cached_rows):
            await _refresh_financial_report(normalized, report_type)

    cached_news: Any = None
    if not force_refresh:
        cached_news, _ = await _load_symbol_payload_cache(NewsCache, normalized, max_age_seconds=None)
    if force_refresh or not _cache_has_content(cached_news):
        await _get_symbol_news(normalized, refresh=True)

    cached_events: Any = None
    if not force_refresh:
        cached_events, _ = await _load_symbol_payload_cache(EventsCache, normalized, max_age_seconds=None)
    if force_refresh or not _cache_has_content(cached_events):
        await _get_symbol_events(normalized, refresh=True)

    cached_technical, _ = await _load_technical_cache(normalized, start_date=None, end_date=None, limit=365)
    if force_refresh or cached_technical is None:
        records = await fetcher_service.load_history_from_db_async(normalized, start_date=None, end_date=None, limit=365)
        if records:
            payload = _calculate_technical_payload(normalized, records)
            await _save_technical_cache(
                normalized,
                start_date=None,
                end_date=None,
                limit=365,
                history_count=len(records),
                history_last_time=str(records[-1].get("time")),
                payload=payload,
            )


async def _preload_reference_caches(symbols: list[str], force_refresh: bool) -> None:
    if not symbols:
        return

    started_at = _utc_now()
    total = len(symbols)
    logger.info("Starting reference cache preload. symbols=%s force_refresh=%s", total, force_refresh)

    for index, symbol in enumerate(symbols, start=1):
        try:
            await _preload_symbol_reference_cache(symbol, force_refresh=force_refresh)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Reference cache preload failed for %s: %s", symbol, exc)

        if index % 5 == 0 or index == total:
            logger.info("Reference cache preload progress: %s/%s", index, total)

    elapsed_seconds = (_utc_now() - started_at).total_seconds()
    logger.info("Reference cache preload completed in %.1fs", elapsed_seconds)


async def _run_reference_preload_after_history(
    history_task: asyncio.Task[Any],
    symbols: list[str],
    force_refresh: bool,
) -> None:
    try:
        await history_task
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.warning("History preload encountered error before reference preload: %s", exc)

    await _preload_reference_caches(symbols=symbols, force_refresh=force_refresh)


lifespan = build_lifespan(
    init_db=init_db,
    fetcher_service=fetcher_service,
    fundamental_service=fundamental_service,
    vn30_symbols=VN30_SYMBOLS,
    preload_reference_cache_enabled=PRELOAD_REFERENCE_CACHE_ENABLED,
    preload_reference_force_refresh=PRELOAD_REFERENCE_FORCE_REFRESH,
    preload_reference_symbol_limit=PRELOAD_REFERENCE_SYMBOL_LIMIT,
)


app = FastAPI(title="VNStock Intraday API V2", lifespan=lifespan, version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API Routers ─────────────────────────────────────────────
from src.api.auth import router as auth_router
from src.api.payment import router as payment_router
from src.api.admin import router as admin_router
from src.api.portfolio import router as portfolio_router

app.include_router(auth_router)
app.include_router(payment_router)
app.include_router(admin_router)
app.include_router(portfolio_router)


class SaveQuotePayload(BaseModel):
    symbol: str = Field(min_length=1, max_length=10)
    price: float
    change: float = 0.0
    changePercent: float = 0.0
    volume: int = 0
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    time: str


def _validate_vn30_symbol(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    if not is_vn30_symbol(normalized):
        raise HTTPException(status_code=404, detail=f"Unsupported symbol '{symbol}'. Only VN30 symbols are allowed.")
    return normalized


async def _ensure_history_data(
    symbol: str,
    start_date: Optional[date],
    end_date: Optional[date],
    limit: int,
) -> list[dict[str, Any]]:
    records = await fetcher_service.load_history_from_db_async(symbol, start_date=start_date, end_date=end_date, limit=limit)
    if records:
        return records

    await fetcher_service.refresh_history_for_symbol(
        symbol,
        start_date=start_date,
        end_date=end_date,
        lookback_days=max(limit, 365),
    )
    return await fetcher_service.load_history_from_db_async(symbol, start_date=start_date, end_date=end_date, limit=limit)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(text("SELECT 1"))
            return {"status": "ok", "database": "mysql-connected"}
        except Exception as exc:
            logger.error("Health check DB error: %s", exc)
            return {"status": "error", "database": f"mysql-error:{exc.__class__.__name__}"}


@app.post("/api/analysis/{symbol}/generate")
async def generate_analysis(
    symbol: str,
    user_id: Optional[int] = Query(default=None, description="User ID (optional)"),
    force: bool = Query(default=False, description="Force refresh from Kaggle model"),
) -> dict[str, Any]:
    """Call Kaggle Trading-R1 model to generate analysis for a stock symbol with rich data."""
    
    symbol = symbol.upper()
    if symbol not in VN30_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not in VN30 list")
    
    kaggle_api_url = os.getenv("KAGGLE_API_URL", "").strip()
    if not kaggle_api_url:
        raise HTTPException(status_code=503, detail="KAGGLE_API_URL not configured")
    
    try:
        # 1. Get real-time market data
        snapshots = fetcher_service.get_snapshots([symbol])
        if not snapshots or len(snapshots) == 0:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        snapshot = snapshots[0]
        current_price = snapshot.get("price", 0)
        price_change = snapshot.get("priceChange", 0)
        price_change_pct = snapshot.get("priceChangePercent", 0)
        volume = snapshot.get("volume", 0)
        market_cap = snapshot.get("marketCap", "N/A")
        
        # 1.5. Get historical data from DB (last 30 days)
        history = await _ensure_history_data(symbol, start_date=None, end_date=None, limit=30)
        price_trend = ""
        history_summary = f"Historical data: {len(history) if history else 0} days loaded"
        
        if history and len(history) > 0:
            # Get last 10 days of prices
            last_10 = history[-10:] if len(history) >= 10 else history
            closes = [float(h.get("close", 0)) for h in last_10]
            
            if len(closes) >= 2:
                high_10d = max(closes)
                low_10d = min(closes)
                avg_10d = sum(closes) / len(closes)
                trend_direction = "UP" if closes[-1] > closes[0] else "DOWN"
                trend_pct = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] > 0 else 0
                
                price_trend = f"""
PRICE TREND (10D History from DB):
- High: {high_10d:.2f} VND
- Low: {low_10d:.2f} VND
- Avg: {avg_10d:.2f} VND
- Direction: {trend_direction} ({trend_pct:+.2f}%)
- Last 5 closes: {[f'{p:.2f}' for p in closes[-5:]]}
"""
        
        # 2. Get technical analysis data via cache
        technical_info = ""
        try:
            # Get technical data from cache function
            cached_row, tech_payload = await _load_technical_cache(
                symbol,
                start_date=None,
                end_date=None,
                limit=365,
            )
            
            if tech_payload and isinstance(tech_payload, dict):
                indicators = tech_payload.get("indicators", {})
                
                # Extract latest values - RSI might be array or scalar
                sma7 = indicators.get("sma_7")
                sma21 = indicators.get("sma_21")
                rsi = indicators.get("rsi_14")
                macd = indicators.get("macd")
                signal = indicators.get("signal")
                
                # Handle RSI if it's an array - get last value
                if isinstance(rsi, list) and len(rsi) > 0:
                    rsi = rsi[-1]
                if isinstance(macd, list) and len(macd) > 0:
                    macd = macd[-1]
                if isinstance(signal, list) and len(signal) > 0:
                    signal = signal[-1]
                
                # Format values safely
                sma7_str = f"{sma7:.2f}" if isinstance(sma7, (int, float)) else "N/A"
                sma21_str = f"{sma21:.2f}" if isinstance(sma21, (int, float)) else "N/A"
                rsi_str = f"{rsi:.1f}" if isinstance(rsi, (int, float)) else "N/A"
                macd_str = f"{macd:.4f}" if isinstance(macd, (int, float)) else "N/A"
                signal_str = f"{signal:.4f}" if isinstance(signal, (int, float)) else "N/A"
                
                technical_info = f"""
TECHNICAL ANALYSIS:
- SMA 7: {sma7_str} VND
- SMA 21: {sma21_str} VND
- RSI 14: {rsi_str}
- MACD: {macd_str}
- Signal Line: {signal_str}
- Interpretation: Multiple technical indicators available for analysis
"""
            else:
                technical_info = "TECHNICAL ANALYSIS: Limited indicator data (no indicators found)"
        except Exception as e:
            logger.warning(f"Could not load technical data for {symbol}: {e}")
            technical_info = "TECHNICAL ANALYSIS: Limited indicator data (exception)"
        
        # 3. Get company overview (fundamentals)
        overview_data = "FUNDAMENTALS: Not available"
        try:
            overview_payload, _ = await fundamental_service.refresh_company_overview(symbol)
            ratio_records, _ = await fundamental_service.refresh_financial_report(symbol, "ratios")
            valuation = _extract_valuation_from_ratios(ratio_records)

            profile = overview_payload if isinstance(overview_payload, dict) else {}
            company_profile = profile.get("company_profile")

            company_name = profile.get("company_name", profile.get("companyName", symbol))
            industry = profile.get("industry", "N/A")
            pe_ratio = valuation.get("pe", "N/A")
            pb_ratio = valuation.get("pb", "N/A")
            eps = valuation.get("eps", "N/A")
            roe = valuation.get("roe", "N/A")
            roa = valuation.get("roa", "N/A")
            market_cap_value = valuation.get("market_cap", profile.get("market_cap", "N/A"))

            overview_data = f"""
FUNDAMENTALS:
- Company: {company_name}
- Industry: {industry}
- P/E Ratio: {pe_ratio}
- P/B Ratio: {pb_ratio}
- EPS: {eps}
- ROE: {roe}
- ROA: {roa}
- Market Cap: {market_cap_value}
- Profile Summary: {str(company_profile)[:300] if company_profile else 'N/A'}
"""
        except Exception as e:
            logger.warning(f"Could not load fundamentals for {symbol}: {e}")
        
        # 4. Get recent news
        news_data = "RECENT NEWS: Not available"
        try:
            news_list, _ = await fundamental_service.get_symbol_news(symbol, refresh=False)
            
            if news_list and len(news_list) > 0:
                recent_news = news_list[:3]  # Last 3 news
                news_items = "\n".join([
                    f"- {news.get('title', 'N/A')} ({news.get('publish_time', news.get('time', 'N/A'))})"
                    for news in recent_news
                ])
                news_data = f"""
RECENT NEWS:
{news_items}
"""
        except Exception as e:
            logger.warning(f"Could not load news for {symbol}: {e}")
        
        logger.info("[ANALYSIS_CONTEXT] fundamentals=%s | news=%s", overview_data.replace("\n", " | "), news_data.replace("\n", " | "))

        # 5. Build comprehensive analysis prompt
        user_prompt = f"""
ANALYZE {symbol} STOCK - PROVIDE INVESTMENT DECISION

REAL-TIME MARKET DATA:
- Current Price: {current_price:.2f} VND
- Price Change: {price_change:+.2f} VND ({price_change_pct:+.2f}%)
- Volume: {volume:,.0f}
- Market Cap: {market_cap}

{price_trend}

{technical_info}

{overview_data}

{news_data}

DATA SOURCE: MySQL database {history_summary}

TASK:
Based on ALL the above data (real-time price, historical trends, technical indicators, fundamentals, news), provide:
1. Investment Decision: BUY, SELL, or HOLD
2. Confidence Level: 0-100 (higher = more confident)
3. Detailed reasoning explaining your decision
4. Key factors influencing the decision

Format your response as JSON with keys: decision, confidence, conclusion
"""
        
        # Debug: Log the prompt before sending
        logger.info(f"[PROMPT_DEBUG] Sending prompt to Kaggle:\n{user_prompt}\n---END PROMPT---")
        
        # 6. Call Kaggle Trading-R1 model
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{kaggle_api_url}/api/analyze",
                json={"prompt": user_prompt},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"Kaggle API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=503, detail=f"Kaggle API error: {response.status_code}")
            
            analysis_result = response.json()
        
        # 7. Parse Kaggle response
        decision = analysis_result.get("decision", "HOLD").upper()
        confidence = float(analysis_result.get("confidence", 50))
        # Normalize confidence to 0-1 if it's 0-100
        if confidence > 1:
            confidence = confidence / 100.0
        reasoning = analysis_result.get("conclusion", analysis_result.get("reasoning", ""))
        raw_output = _extract_kaggle_output_text(analysis_result)
        key_factors = _extract_kaggle_key_factors(raw_output)
        if not reasoning and raw_output:
            reasoning = raw_output
        
        # Validate decision value
        if decision not in ["BUY", "SELL", "HOLD"]:
            decision = "HOLD"
        
        # 8. Save to database
        async with AsyncSessionLocal() as db:
            ai_pred = AIPrediction(
                user_id=user_id,
                symbol=symbol,
                prediction=decision,
                confidence=confidence,
                reasoning=reasoning,
                model_version="Trading-R1/Qwen3.5-2B"
            )
            db.add(ai_pred)
            await db.commit()
        
        return {
            "status": "ok",
            "symbol": symbol,
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "raw_output": raw_output,
            "key_factors": key_factors,
            "current_price": current_price,
            "analysis": {
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "volume": volume,
                "days_analyzed": len(history) if history else 0,
                "data_source": "MySQL (history) + vnstock (live) + Kaggle Trading-R1 (analysis)"
            },
            "model_version": "Trading-R1/Qwen3.5-2B"
        }
    
    except httpx.RequestError as exc:
        logger.error(f"Kaggle API connection error: {exc}")
        raise HTTPException(status_code=503, detail=f"Kaggle API connection error: {str(exc)}")
    except Exception as exc:
        logger.error(f"Analysis generation error: {exc}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(exc)}")


@app.get("/api/stocks")
def list_stocks() -> dict[str, list[str]]:
    return {"tickers": VN30_SYMBOLS}


@app.get("/api/stocks/snapshots")
async def get_snapshots(
    symbols: Optional[str] = Query(default=None, description="Comma-separated symbols"),
    refresh: bool = Query(default=False, description="Force refresh from vnstock before returning"),
) -> dict[str, Any]:
    target_symbols = parse_symbols_query(symbols, fallback=VN30_SYMBOLS)
    in_session = fetcher_service.is_intraday_fetch_window()
    auto_refresh = in_session and _intraday_cache_is_stale()
    should_refresh = refresh or auto_refresh

    if should_refresh:
        await _safe_refresh_symbols_once(target_symbols)

    snapshots = fetcher_service.get_snapshots(target_symbols)
    synced_candidates = [
        item.get("syncedAt")
        for item in snapshots
        if isinstance(item.get("syncedAt"), str) and item.get("syncedAt")
    ]
    latest_sync = fetcher_service.last_intraday_sync_at or (max(synced_candidates) if synced_candidates else None)

    return {
        "count": len(snapshots),
        "data": snapshots,
        "cached_at": datetime.utcnow().isoformat(),
        "last_synced_at": latest_sync,
        "source": "vnstock-v2",
        "refreshed": should_refresh,
        "auto_refreshed": auto_refresh and not refresh,
        "is_in_session": in_session,
        "cache_age_seconds": _intraday_cache_age_seconds(),
    }


@app.get("/api/stocks/{symbol}/overview")
async def get_overview(
    symbol: str,
    refresh: bool = Query(default=False, description="Force refresh overview and valuation from vnstock"),
) -> dict[str, Any]:
    normalized = _validate_vn30_symbol(symbol)
    snapshot = fetcher_service.get_snapshot(normalized)

    overview_payload: dict[str, Any] = {}
    overview_synced_at: Optional[str] = None
    if not refresh:
        cached_overview, cached_synced_at = await _load_symbol_payload_cache(
            CompanyOverviewCache,
            normalized,
            max_age_seconds=None,
        )
        if isinstance(cached_overview, dict):
            overview_payload = dict(cached_overview)
            overview_synced_at = cached_synced_at

    if refresh or not overview_payload:
        refreshed_overview, refreshed_synced_at = await fundamental_service.refresh_company_overview(normalized)
        if refreshed_overview:
            overview_payload = dict(refreshed_overview)
            overview_synced_at = refreshed_synced_at

    ratio_records: list[dict[str, Any]] = []
    ratios_synced_at: Optional[str] = None
    if not refresh:
        cached_ratios, cached_ratio_synced_at = await _load_financial_report_cache(
            normalized,
            "ratios",
            max_age_seconds=None,
        )
        if isinstance(cached_ratios, list):
            ratio_records = list(cached_ratios)
            ratios_synced_at = cached_ratio_synced_at

    if refresh or not ratio_records:
        refreshed_ratios, refreshed_ratio_synced_at = await fundamental_service.refresh_financial_report(normalized, "ratios")
        if refreshed_ratios:
            ratio_records = list(refreshed_ratios)
            ratios_synced_at = refreshed_ratio_synced_at

    valuation = _extract_valuation_from_ratios(ratio_records)
    company_name = (
        str(
            overview_payload.get("company_name")
            or overview_payload.get("companyName")
            or overview_payload.get("name")
            or normalized
        )
        .strip()
        or normalized
    )
    industry = (
        str(
            overview_payload.get("industry")
            or overview_payload.get("icb_name2")
            or overview_payload.get("icb_name3")
            or "VN30"
        )
        .strip()
        or "VN30"
    )

    sync_candidates = [snapshot.get("syncedAt"), overview_synced_at, ratios_synced_at]
    last_synced_at = max([item for item in sync_candidates if isinstance(item, str) and item], default=None)

    return {
        "symbol": normalized,
        "company_name": company_name,
        "companyName": company_name,
        "exchange": "HOSE",
        "industry": industry,
        "company_profile": overview_payload.get("company_profile"),
        "charter_capital": _to_number_or_none(overview_payload.get("charter_capital")),
        "issue_share": _to_number_or_none(overview_payload.get("issue_share")),
        "price": _to_float(snapshot.get("price")),
        "change": _to_float(snapshot.get("change")),
        "change_percent": _to_float(snapshot.get("changePercent")),
        "volume": int(_to_float(snapshot.get("volume"))),
        "pe": valuation.get("pe"),
        "pb": valuation.get("pb"),
        "eps": valuation.get("eps"),
        "roe": valuation.get("roe"),
        "roa": valuation.get("roa"),
        "market_cap": valuation.get("market_cap"),
        "last_update": snapshot.get("lastUpdate"),
        "source": "mysql-cache+vnstock",
        "last_synced_at": last_synced_at,
    }


@app.get("/api/stocks/{symbol}/history")
async def get_history(
    symbol: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    limit: int = Query(default=365, ge=1, le=5000),
    refresh: bool = Query(default=False, description="Force refresh historical data from vnstock before reading MySQL"),
) -> dict[str, Any]:
    normalized = _validate_vn30_symbol(symbol)
    if refresh:
        await fetcher_service.refresh_history_for_symbol(
            normalized,
            start_date=start_date,
            end_date=end_date,
            lookback_days=max(limit, 365),
        )

    records = await _ensure_history_data(normalized, start_date=start_date, end_date=end_date, limit=limit)

    return {
        "symbol": normalized,
        "count": len(records),
        "data": records,
        "source": "mysql-history-refresh" if refresh else "mysql",
        "last_synced_at": fetcher_service.last_history_sync_at.get(normalized),
    }


@app.get("/api/stocks/{symbol}/intraday")
async def get_intraday(
    symbol: str,
    limit: int = Query(default=320, ge=10, le=2000),
    interval_minutes: int = Query(default=1, ge=1, le=30),
    refresh: bool = Query(default=False, description="Force refresh intraday from vnstock before reading cache"),
    force: bool = Query(default=False, description="Allow refresh outside trading session windows (debug)"),
) -> dict[str, Any]:
    normalized = _validate_vn30_symbol(symbol)
    refreshed = False

    if refresh:
        refreshed = await _safe_refresh_symbol(normalized, ignore_session=force)

    tick_window = min(max(limit * max(interval_minutes, 1) * 12, 600), 5000)
    cache_payload = fetcher_service.get_intraday_cache_view(symbols=[normalized], limit=tick_window)
    ticks = cache_payload.get(normalized, [])
    bars = _build_intraday_bars_from_ticks(ticks, interval_minutes=interval_minutes)

    if len(bars) > limit:
        bars = bars[-limit:]

    return {
        "symbol": normalized,
        "count": len(bars),
        "ticks_count": len(ticks),
        "data": bars,
        "interval_minutes": interval_minutes,
        "source": "intraday-cache-refresh" if refresh else "intraday-cache",
        "last_synced_at": fetcher_service.last_intraday_sync_at,
        "is_in_session": fetcher_service.is_intraday_fetch_window(),
        "refreshed": bool(refreshed),
        "forced": force,
    }


@app.get("/api/stocks/{symbol}/ticks")
async def get_ticks(
    symbol: str,
    limit: int = Query(default=100, ge=1, le=1000),
    refresh: bool = Query(default=False),
    force: bool = Query(default=False),
) -> dict[str, Any]:
    """Return raw intraday trade ticks (sổ lệnh — matched orders) for a symbol."""
    normalized = _validate_vn30_symbol(symbol)
    in_session = fetcher_service.is_intraday_fetch_window()
    auto_refresh = in_session and _intraday_cache_is_stale()
    refreshed = False

    if refresh or auto_refresh:
        refreshed = await _safe_refresh_symbol(normalized, ignore_session=force)

    cache_payload = fetcher_service.get_intraday_cache_view(symbols=[normalized], limit=limit)
    ticks: list[dict] = cache_payload.get(normalized, [])

    # Best-effort retry for in-session empty cache to reduce stale UI state.
    if in_session and not ticks and not refreshed:
        refreshed = await _safe_refresh_symbol(normalized, ignore_session=force)
        cache_payload = fetcher_service.get_intraday_cache_view(symbols=[normalized], limit=limit)
        ticks = cache_payload.get(normalized, [])

    # Return most-recent first for order log display.
    ticks_desc = sorted(
        ticks,
        key=lambda item: _parse_datetime(item.get("time"))
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return {
        "symbol": normalized,
        "count": len(ticks_desc),
        "ticks": ticks_desc,
        "is_in_session": in_session,
        "last_synced_at": fetcher_service.last_intraday_sync_at,
        "refreshed": bool(refreshed),
        "auto_refreshed": auto_refresh and not refresh,
        "cache_age_seconds": _intraday_cache_age_seconds(),
    }


@app.get("/api/stocks/{symbol}/technical")
async def get_technical(
    symbol: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    limit: int = Query(default=365, ge=30, le=5000),
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    normalized = _validate_vn30_symbol(symbol)
    records = await _ensure_history_data(normalized, start_date=start_date, end_date=end_date, limit=limit)

    history_count = len(records)
    history_last_time = str(records[-1].get("time")) if records else None

    if not refresh:
        cached_row, cached_payload = await _load_technical_cache(
            normalized,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        if (
            cached_row
            and cached_payload
            and cached_row.history_count == history_count
            and (cached_row.history_last_time or None) == history_last_time
            and _row_is_fresh(cached_row.updated_at, TECHNICAL_CACHE_TTL_SECONDS)
        ):
            payload = dict(cached_payload)
            payload["source"] = "mysql-technical-cache"
            payload["last_synced_at"] = fetcher_service.last_history_sync_at.get(normalized) or _row_iso_timestamp(cached_row.updated_at)
            return payload

    payload = _calculate_technical_payload(normalized, records)
    technical_synced_at = await _save_technical_cache(
        normalized,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        history_count=history_count,
        history_last_time=history_last_time,
        payload=payload,
    )
    payload["source"] = "mysql"
    payload["last_synced_at"] = fetcher_service.last_history_sync_at.get(normalized) or technical_synced_at
    return payload


@app.get("/api/stocks/{symbol}/financials")
async def get_financials(
    symbol: str,
    report_type: str = Query(default="income", pattern="^(income|balance|cashflow|ratios)$"),
    refresh: bool = Query(default=False, description="Force refresh financial report from vnstock"),
) -> dict[str, Any]:
    normalized = _validate_vn30_symbol(symbol)

    cached_rows: Optional[list[dict[str, Any]]] = None
    cached_synced_at: Optional[str] = None
    if not refresh:
        cached_rows, cached_synced_at = await _load_financial_report_cache(
            normalized,
            report_type,
            max_age_seconds=None,
        )

    if not refresh and cached_rows is not None:
        return {
            "symbol": normalized,
            "type": report_type,
            "count": len(cached_rows),
            "data": cached_rows,
            "source": "mysql-financial-cache",
            "last_synced_at": cached_synced_at,
        }

    rows, synced_at = await fundamental_service.refresh_financial_report(normalized, report_type)
    if rows:
        return {
            "symbol": normalized,
            "type": report_type,
            "count": len(rows),
            "data": rows,
            "source": f"vnstock-finance-{report_type}",
            "last_synced_at": synced_at,
        }

    stale_rows, stale_synced_at = await _load_financial_report_cache(
        normalized,
        report_type,
        max_age_seconds=None,
    )
    if stale_rows is None:
        stale_rows = []

    return {
        "symbol": normalized,
        "type": report_type,
        "count": len(stale_rows),
        "data": stale_rows,
        "source": "mysql-financial-cache-stale",
        "last_synced_at": stale_synced_at,
    }


@app.get("/api/market-indices")
async def get_market_indices(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    refresh: bool = Query(default=False, description="Force refresh index prices from vnstock"),
) -> dict[str, Any]:
    target_symbols = MARKET_INDEX_ORDER[: min(limit, len(MARKET_INDEX_ORDER))]

    index_rows: list[dict[str, Any]] = []
    source_parts: set[str] = set()
    synced_at_values: list[str] = []
    for index_symbol in target_symbols:
        history_rows, synced_at, data_source = await _get_market_index_history_rows(
            index_symbol=index_symbol,
            start_date=start_date,
            end_date=end_date,
            limit=max(3, min(120, limit * 10)),
            refresh=refresh,
        )
        index_rows.append(_build_market_index_quote(index_symbol=index_symbol, history_rows=history_rows))
        source_parts.add(data_source)
        if synced_at:
            synced_at_values.append(synced_at)

    return {
        "count": len(index_rows),
        "data": index_rows,
        "source": "+".join(sorted(source_parts)) if source_parts else "vnstock-market-index-unavailable",
        "last_synced_at": max(synced_at_values) if synced_at_values else None,
    }


@app.get("/api/market-indices/{index_symbol}/history")
async def get_market_index_history(
    index_symbol: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    limit: int = Query(default=365, ge=30, le=5000),
    refresh: bool = Query(default=False, description="Force refresh index history from vnstock"),
) -> dict[str, Any]:
    normalized = _normalize_market_index_symbol(index_symbol)
    history_rows, synced_at, source = await _get_market_index_history_rows(
        index_symbol=normalized,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        refresh=refresh,
    )

    definition = MARKET_INDEX_DEFINITIONS[normalized]
    return {
        "symbol": normalized,
        "name": definition["name"],
        "count": len(history_rows),
        "data": history_rows,
        "source": source,
        "last_synced_at": synced_at,
    }


@app.get("/api/news")
async def get_news(
    symbols: Optional[str] = Query(default=None),
    limit: int = Query(default=24, ge=1, le=200),
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    target = parse_symbols_query(symbols, fallback=VN30_SYMBOLS[:8])
    merged: list[dict[str, Any]] = []
    synced_at_values: list[str] = []

    for symbol in target:
        items, synced_at = await fundamental_service.get_symbol_news(symbol, refresh=refresh)
        merged.extend(items)
        if synced_at:
            synced_at_values.append(synced_at)

    merged.sort(key=lambda item: item.get("publish_time") or "", reverse=True)
    clipped = merged[:limit]

    return {
        "count": len(clipped),
        "symbols": target,
        "data": clipped,
        "cached_at": _utc_now().isoformat(),
        "source": "mysql-cache+vnstock-company-news",
        "last_synced_at": max(synced_at_values) if synced_at_values else None,
        "limit": limit,
    }


@app.get("/api/events")
async def get_events(
    symbols: Optional[str] = Query(default=None),
    limit: int = Query(default=24, ge=1, le=200),
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    target = parse_symbols_query(symbols, fallback=VN30_SYMBOLS[:8])
    merged: list[dict[str, Any]] = []
    synced_at_values: list[str] = []

    for symbol in target:
        items, synced_at = await fundamental_service.get_symbol_events(symbol, refresh=refresh)
        merged.extend(items)
        if synced_at:
            synced_at_values.append(synced_at)

    today = _utc_now().date()
    future_events = [item for item in merged if (_parse_datetime(item.get("date")) or _utc_now()).date() >= today]
    past_events = [item for item in merged if (_parse_datetime(item.get("date")) or _utc_now()).date() < today]

    future_events.sort(key=lambda item: item.get("date") or "")
    past_events.sort(key=lambda item: item.get("date") or "", reverse=True)
    clipped = (future_events + past_events)[:limit]

    return {
        "count": len(clipped),
        "symbols": target,
        "data": clipped,
        "cached_at": _utc_now().isoformat(),
        "source": "mysql-cache+vnstock-company-events",
        "last_synced_at": max(synced_at_values) if synced_at_values else None,
        "limit": limit,
    }


@app.post("/api/dnse/save-quotes")
async def save_quotes(quotes: list[SaveQuotePayload]) -> dict[str, int]:
    if not quotes:
        return {"saved": 0}

    payloads = [item.model_dump() for item in quotes]
    saved = await fetcher_service.ingest_realtime_quotes(payloads)
    return {"saved": saved}


@app.post("/api/debug/intraday/refresh")
async def debug_refresh_intraday(
    symbols: Optional[str] = Query(default=None, description="Comma-separated VN30 symbols"),
    force: bool = Query(default=True, description="Allow refresh outside trading session windows"),
    cache_limit: int = Query(default=240, ge=1, le=2000),
) -> dict[str, Any]:
    target_symbols = parse_symbols_query(symbols, fallback=VN30_SYMBOLS)
    updated = await fetcher_service.refresh_symbols_once(target_symbols, ignore_session=force)
    cache_payload = fetcher_service.get_intraday_cache_view(symbols=target_symbols, limit=cache_limit)
    per_symbol_tick_counts = {
        symbol: len(cache_payload.get(symbol, []))
        for symbol in target_symbols
    }

    return {
        "count": len(target_symbols),
        "symbols": target_symbols,
        "updated_symbols": updated,
        "forced": force,
        "is_in_session": fetcher_service.is_intraday_fetch_window(),
        "last_synced_at": fetcher_service.last_intraday_sync_at,
        "total_ticks": sum(per_symbol_tick_counts.values()),
        "per_symbol_tick_counts": per_symbol_tick_counts,
    }


@app.websocket("/api/ws/dnse")
async def websocket_dnse_compatible(websocket: WebSocket):
    await websocket.accept()
    subscribed_symbols: set[str] = set()

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                incoming = json.loads(raw)

                if str(incoming.get("type", "")).lower() == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                action = str(incoming.get("action", "")).lower()
                data = incoming.get("data") if isinstance(incoming.get("data"), dict) else {}
                symbol = normalize_symbol(str(data.get("symbol", "")))

                if action == "subscribe" and is_vn30_symbol(symbol):
                    subscribed_symbols.add(symbol)
                elif action == "unsubscribe" and symbol:
                    subscribed_symbols.discard(symbol)
            except asyncio.TimeoutError:
                pass
            except json.JSONDecodeError:
                continue

            if not subscribed_symbols:
                await websocket.send_json({"type": "heartbeat"})
                continue

            snapshots = fetcher_service.get_snapshots(sorted(subscribed_symbols))
            for snapshot in snapshots:
                if _to_float(snapshot.get("price")) <= 0:
                    continue
                await websocket.send_json(
                    {
                        "symbol": snapshot.get("symbol"),
                        "price": _to_float(snapshot.get("price")),
                        "change": _to_float(snapshot.get("change")),
                        "changePercent": _to_float(snapshot.get("changePercent")),
                        "volume": int(_to_float(snapshot.get("volume"))),
                        "high": _to_float(snapshot.get("high")),
                        "low": _to_float(snapshot.get("low")),
                        "open": _to_float(snapshot.get("open")),
                        "time": str(snapshot.get("lastUpdate") or datetime.utcnow().isoformat()),
                    }
                )
    except WebSocketDisconnect:
        logger.info("Client disconnected from /api/ws/dnse")


@app.websocket("/api/ws/market")
async def websocket_market_cache(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            payload = {
                "action": "update",
                "data": fetcher_service.get_intraday_cache_view(limit=120),
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("Client disconnected from /api/ws/market")
