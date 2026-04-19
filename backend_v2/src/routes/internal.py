"""
Internal / debug routes – /api/dnse/* and /api/debug/*

Provides quote ingestion from DNSE and manual intraday refresh for debugging.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from src.api.auth import require_role
from src.database.models import User
from src.services.vnstock_fetcher import VN30_SYMBOLS, fetcher_service, parse_symbols_query

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Internal"])


# ── Pydantic models ───────────────────────────────────────────────────


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


# ── Routes ────────────────────────────────────────────────────────────


@router.post("/api/dnse/save-quotes")
async def save_quotes(
    quotes: list[SaveQuotePayload],
    _: User = Depends(require_role("admin")),
) -> dict[str, int]:
    if not quotes:
        return {"saved": 0}

    payloads = [item.model_dump() for item in quotes]
    saved = await fetcher_service.ingest_realtime_quotes(payloads)
    return {"saved": saved}


@router.post("/api/debug/intraday/refresh")
async def debug_refresh_intraday(
    symbols: Optional[str] = Query(default=None, description="Comma-separated VN30 symbols"),
    force: bool = Query(default=True, description="Allow refresh outside trading session windows"),
    cache_limit: int = Query(default=240, ge=1, le=2000),
    _: User = Depends(require_role("admin")),
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
