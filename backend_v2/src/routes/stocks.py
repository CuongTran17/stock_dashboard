"""
Stock routes – /api/stocks/*

Covers: list, snapshots, overview, history, intraday, ticks, technical
indicators, and financial reports.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.cache import (
    _load_financial_report_cache,
    _load_symbol_payload_cache,
    _load_technical_cache,
    _save_technical_cache,
)
from src.database.models import CompanyOverviewCache
from src.market_data_status import DATA_AVAILABLE, NO_DATA_IN_SNAPSHOT, reject_refresh_in_snapshot_mode
from src.services.vnstock_fetcher import (
    VN30_SYMBOLS,
    fetcher_service,
    is_vn30_symbol,
    normalize_symbol,
    parse_symbols_query,
)
from src.services.technical_indicators import build_technical_payload
from src.settings import get_settings
from src.utils import (
    _build_intraday_bars_from_ticks,
    _extract_valuation_from_ratios,
    _parse_datetime,
    _row_is_fresh,
    _row_iso_timestamp,
    _to_float,
    _to_number_or_none,
    _utc_now,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Constants (mirror from main until fully extracted)
INTRADAY_STALE_SECONDS = settings.vnstock_intraday_stale_seconds
TECHNICAL_CACHE_TTL_SECONDS = settings.vnstock_technical_cache_ttl_seconds

router = APIRouter(tags=["Stocks"])


# ── Intraday cache helpers (depend on fetcher_service) ────────────────


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


# ── Private helpers ───────────────────────────────────────────────────


def _validate_vn30_symbol(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    if not is_vn30_symbol(normalized):
        raise HTTPException(status_code=404, detail=f"Unsupported symbol '{symbol}'. Only VN30 symbols are allowed.")
    return normalized


async def _load_history_data(
    symbol: str,
    start_date: Optional[date],
    end_date: Optional[date],
    limit: int,
) -> list[dict[str, Any]]:
    return await fetcher_service.load_history_from_db_async(
        symbol,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


def _calculate_technical_payload(symbol: str, history: list[dict[str, Any]]) -> dict[str, Any]:
    frame = pd.DataFrame(history)
    return build_technical_payload(
        symbol,
        frame,
        time_col="time",
        open_col="open",
        high_col="high",
        low_col="low",
        close_col="close",
        volume_col="volume",
    )


# ── Routes ────────────────────────────────────────────────────────────


@router.get("/api/stocks")
def list_stocks() -> dict[str, list[str]]:
    return {"tickers": VN30_SYMBOLS}


@router.get("/api/stocks/snapshots")
async def get_snapshots(
    symbols: Optional[str] = Query(default=None, description="Comma-separated symbols"),
    refresh: bool = Query(default=False, description="Force refresh from vnstock before returning"),
) -> dict[str, Any]:
    reject_refresh_in_snapshot_mode(refresh)
    target_symbols = parse_symbols_query(symbols, fallback=VN30_SYMBOLS)
    in_session = fetcher_service.is_intraday_fetch_window()
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
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "last_synced_at": latest_sync,
        "source": "snapshot-mysql-cache",
        "refreshed": False,
        "auto_refreshed": False,
        "is_in_session": in_session,
        "cache_age_seconds": _intraday_cache_age_seconds(),
        "data_status": DATA_AVAILABLE if snapshots else NO_DATA_IN_SNAPSHOT,
    }


@router.get("/api/stocks/{symbol}/overview")
async def get_overview(
    symbol: str,
    refresh: bool = Query(default=False, description="Force refresh overview and valuation from vnstock"),
) -> dict[str, Any]:
    reject_refresh_in_snapshot_mode(refresh)
    normalized = _validate_vn30_symbol(symbol)
    snapshot = fetcher_service.get_snapshot(normalized)

    overview_payload: dict[str, Any] = {}
    overview_synced_at: Optional[str] = None
    cached_overview, cached_synced_at = await _load_symbol_payload_cache(
        CompanyOverviewCache,
        normalized,
        max_age_seconds=None,
    )
    if isinstance(cached_overview, dict):
        overview_payload = dict(cached_overview)
        overview_synced_at = cached_synced_at

    ratio_records: list[dict[str, Any]] = []
    ratios_synced_at: Optional[str] = None
    cached_ratios, cached_ratio_synced_at = await _load_financial_report_cache(
        normalized,
        "ratios",
        max_age_seconds=None,
    )
    if isinstance(cached_ratios, list):
        ratio_records = list(cached_ratios)
        ratios_synced_at = cached_ratio_synced_at

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
        "source": "mysql-cache",
        "last_synced_at": last_synced_at,
        "data_status": DATA_AVAILABLE if overview_payload or ratio_records else NO_DATA_IN_SNAPSHOT,
    }


@router.get("/api/stocks/{symbol}/history")
async def get_history(
    symbol: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    limit: int = Query(default=365, ge=1, le=5000),
    refresh: bool = Query(default=False, description="Force refresh historical data from vnstock before reading DuckDB"),
) -> dict[str, Any]:
    reject_refresh_in_snapshot_mode(refresh)
    normalized = _validate_vn30_symbol(symbol)
    records = await _load_history_data(normalized, start_date=start_date, end_date=end_date, limit=limit)

    return {
        "symbol": normalized,
        "count": len(records),
        "data": records,
        "source": "duckdb",
        "last_synced_at": fetcher_service.last_history_sync_at.get(normalized),
        "data_status": DATA_AVAILABLE if records else NO_DATA_IN_SNAPSHOT,
    }


@router.get("/api/stocks/{symbol}/intraday")
async def get_intraday(
    symbol: str,
    limit: int = Query(default=320, ge=10, le=2000),
    interval_minutes: int = Query(default=1, ge=1, le=30),
    refresh: bool = Query(default=False, description="Force refresh intraday from vnstock before reading cache"),
    force: bool = Query(default=False, description="Allow refresh outside trading session windows (debug)"),
) -> dict[str, Any]:
    reject_refresh_in_snapshot_mode(refresh)
    del force
    normalized = _validate_vn30_symbol(symbol)

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
        "source": "intraday-cache",
        "last_synced_at": fetcher_service.last_intraday_sync_at,
        "is_in_session": fetcher_service.is_intraday_fetch_window(),
        "refreshed": False,
        "forced": False,
        "data_status": DATA_AVAILABLE if bars else NO_DATA_IN_SNAPSHOT,
    }


@router.get("/api/stocks/{symbol}/ticks")
async def get_ticks(
    symbol: str,
    limit: int = Query(default=100, ge=1, le=1000),
    refresh: bool = Query(default=False),
    force: bool = Query(default=False),
) -> dict[str, Any]:
    """Return raw intraday trade ticks (sổ lệnh — matched orders) for a symbol."""
    reject_refresh_in_snapshot_mode(refresh)
    del force
    normalized = _validate_vn30_symbol(symbol)
    in_session = fetcher_service.is_intraday_fetch_window()

    cache_payload = fetcher_service.get_intraday_cache_view(symbols=[normalized], limit=limit)
    ticks: list[dict] = cache_payload.get(normalized, [])

    # Return most-recent first for order log display.
    ticks_desc = sorted(
        ticks,
        key=lambda item: _parse_datetime(item.get("time")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return {
        "symbol": normalized,
        "count": len(ticks_desc),
        "ticks": ticks_desc,
        "is_in_session": in_session,
        "last_synced_at": fetcher_service.last_intraday_sync_at,
        "refreshed": False,
        "auto_refreshed": False,
        "cache_age_seconds": _intraday_cache_age_seconds(),
        "data_status": DATA_AVAILABLE if ticks_desc else NO_DATA_IN_SNAPSHOT,
    }


@router.get("/api/stocks/{symbol}/technical")
async def get_technical(
    symbol: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    limit: int = Query(default=365, ge=30, le=5000),
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    reject_refresh_in_snapshot_mode(refresh)
    normalized = _validate_vn30_symbol(symbol)
    records = await _load_history_data(normalized, start_date=start_date, end_date=end_date, limit=limit)

    if not records:
        return {
            "symbol": normalized,
            "count": 0,
            "ohlcv": {"time": [], "open": [], "high": [], "low": [], "close": [], "volume": []},
            "indicators": {},
            "signals": {},
            "source": "duckdb",
            "last_synced_at": None,
            "data_status": NO_DATA_IN_SNAPSHOT,
        }

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
            payload["source"] = "duckdb-technical-cache"
            payload["last_synced_at"] = fetcher_service.last_history_sync_at.get(normalized) or _row_iso_timestamp(cached_row.updated_at)
            payload["data_status"] = DATA_AVAILABLE
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
    payload["source"] = "duckdb"
    payload["last_synced_at"] = fetcher_service.last_history_sync_at.get(normalized) or technical_synced_at
    payload["data_status"] = DATA_AVAILABLE
    return payload


@router.get("/api/stocks/{symbol}/financials")
async def get_financials(
    symbol: str,
    report_type: str = Query(default="income", pattern="^(income|balance|cashflow|ratios)$"),
    refresh: bool = Query(default=False, description="Force refresh financial report from vnstock"),
) -> dict[str, Any]:
    reject_refresh_in_snapshot_mode(refresh)
    normalized = _validate_vn30_symbol(symbol)

    cached_rows, cached_synced_at = await _load_financial_report_cache(
        normalized,
        report_type,
        max_age_seconds=None,
    )
    rows = cached_rows or []

    return {
        "symbol": normalized,
        "type": report_type,
        "count": len(rows),
        "data": rows,
        "source": "mysql-financial-cache",
        "last_synced_at": cached_synced_at,
        "data_status": DATA_AVAILABLE if rows else NO_DATA_IN_SNAPSHOT,
    }
