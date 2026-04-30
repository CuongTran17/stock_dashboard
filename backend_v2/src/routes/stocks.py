"""
Stock routes – /api/stocks/*

Covers: list, snapshots, overview, history, intraday, ticks, technical
indicators, and financial reports.
"""
from __future__ import annotations

import asyncio
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
from src.services.fundamental_fetcher import fundamental_service
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
INTRADAY_REFRESH_TIMEOUT_SECONDS = settings.vnstock_intraday_refresh_timeout_seconds
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
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "last_synced_at": latest_sync,
        "source": "vnstock-v2",
        "refreshed": should_refresh,
        "auto_refreshed": auto_refresh and not refresh,
        "is_in_session": in_session,
        "cache_age_seconds": _intraday_cache_age_seconds(),
    }


@router.get("/api/stocks/{symbol}/overview")
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


@router.get("/api/stocks/{symbol}/history")
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


@router.get("/api/stocks/{symbol}/intraday")
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


@router.get("/api/stocks/{symbol}/ticks")
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
        key=lambda item: _parse_datetime(item.get("time")) or datetime.min.replace(tzinfo=timezone.utc),
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


@router.get("/api/stocks/{symbol}/technical")
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


@router.get("/api/stocks/{symbol}/financials")
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
