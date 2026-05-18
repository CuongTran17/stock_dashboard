from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.services.dnse_market_data import DnseMarketDataConfigError, get_dnse_market_client
from src.settings import get_settings

router = APIRouter(tags=["DNSE Tick Sandbox"])


def _parse_symbols(raw: str) -> list[str]:
    symbols: list[str] = []
    for token in raw.replace(";", ",").split(","):
        symbol = token.strip().upper()
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols


@router.get("/api/dnse/ticks/status")
async def get_dnse_tick_status() -> dict[str, Any]:
    settings = get_settings()
    client = get_dnse_market_client()
    return {
        "status": "configured" if client.is_configured else "not_configured",
        "configured": client.is_configured,
        "base_url": settings.dnse_market_base_url,
        "board_id": settings.dnse_market_board_id,
        "poll_interval_ms": settings.dnse_tick_poll_interval_ms,
        "endpoint": "/price/{symbol}/trades/latest",
        "auth": "x-api-key + X-Signature",
    }


@router.get("/api/dnse/ticks/latest")
async def get_latest_ticks(
    symbols: str = Query(default="FPT,VCB,VIC", description="Comma-separated symbols"),
) -> dict[str, Any]:
    parsed = _parse_symbols(symbols)
    if not parsed:
        raise HTTPException(status_code=400, detail="No symbols provided")
    if len(parsed) > 30:
        raise HTTPException(status_code=400, detail="Sandbox supports at most 30 symbols")

    client = get_dnse_market_client()
    if not client.is_configured:
        return {
            "status": "not_configured",
            "source": "dnse",
            "symbols": parsed,
            "ticks": [],
            "errors": {
                "config": "Set DNSE_MARKET_API_KEY and DNSE_MARKET_API_SECRET in backend_v2/.env"
            },
            "latency_ms": 0,
        }
    return await client.get_latest_trades(parsed)


@router.get("/api/dnse/ticks/debug")
async def debug_latest_tick(
    symbol: str = Query(default="FPT", min_length=1, max_length=10),
) -> dict[str, Any]:
    client = get_dnse_market_client()
    if not client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Set DNSE_MARKET_API_KEY and DNSE_MARKET_API_SECRET in backend_v2/.env",
        )
    try:
        return await client.get_latest_trade(symbol)
    except DnseMarketDataConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
