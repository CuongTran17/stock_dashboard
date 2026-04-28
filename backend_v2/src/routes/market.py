"""
Market routes – /api/market-indices/*, /api/news, /api/events

Covers market index history/quotes, news feed and corporate events.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from vnstock import Quote

from src.services.fundamental_fetcher import fundamental_service
from src.services.vnstock_fetcher import VN30_SYMBOLS, fetcher_service, parse_symbols_query
from src.utils import (
    _cache_fresh,
    _parse_datetime,
    _to_float,
    _to_int,
    _to_iso_date,
    _utc_now,
)

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[3]

# ── Market index configuration ────────────────────────────────────────

MARKET_INDEX_HISTORY_TTL_SECONDS = max(int(os.getenv("VNSTOCK_MARKET_INDEX_CACHE_TTL_SECONDS", "180")), 30)
MARKET_INDEX_LOOKBACK_DAYS = max(int(os.getenv("VNSTOCK_MARKET_INDEX_LOOKBACK_DAYS", "540")), 120)

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

# ── In-memory caches ──────────────────────────────────────────────────

_market_index_history_cache: dict[str, dict[str, Any]] = {}
_market_index_lock = asyncio.Lock()

router = APIRouter(tags=["Market"])


# ── Private helpers ───────────────────────────────────────────────────


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


# ── Routes ────────────────────────────────────────────────────────────


@router.get("/api/market-indices")
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


@router.get("/api/market-indices/{index_symbol}/history")
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


@router.get("/api/news")
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


def _load_latest_google_news(symbol: str, limit: int) -> tuple[list[dict[str, Any]], Optional[str]]:
    symbol = symbol.upper()
    symbol_dir = REPO_ROOT / "lake" / "raw" / "google_news" / symbol
    if not symbol_dir.exists():
        return [], None

    files = sorted(symbol_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in files:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Could not read google news cache %s", path)
            continue

        if not isinstance(raw, list):
            continue

        items: list[dict[str, Any]] = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            published = item.get("datetime") or item.get("date") or ""
            items.append({
                "id": f"{symbol}-google-{path.stem}-{index}",
                "symbol": symbol,
                "symbols": [symbol],
                "source": str(item.get("source") or "Google News"),
                "title": title,
                "summary": str(item.get("desc") or ""),
                "publish_time": str(published),
                "time": str(published),
                "url": str(item.get("link") or ""),
                "impact": "medium",
            })

        items.sort(key=lambda entry: entry.get("publish_time") or "", reverse=True)
        return items[:limit], datetime.fromtimestamp(path.stat().st_mtime).isoformat()

    return [], None


@router.get("/api/google-news")
async def get_google_news(
    symbols: Optional[str] = Query(default=None),
    limit: int = Query(default=24, ge=1, le=200),
) -> dict[str, Any]:
    target = parse_symbols_query(symbols, fallback=VN30_SYMBOLS[:8])
    merged: list[dict[str, Any]] = []
    synced_at_values: list[str] = []

    per_symbol_limit = max(limit, 1)
    for symbol in target:
        items, synced_at = _load_latest_google_news(symbol, per_symbol_limit)
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
        "source": "lake-raw-google-news",
        "last_synced_at": max(synced_at_values) if synced_at_values else None,
        "limit": limit,
    }


@router.get("/api/events")
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
