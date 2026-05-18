from __future__ import annotations

import base64
import hashlib
import hmac
import time
from datetime import datetime, timezone
from typing import Any
from urllib import parse
from uuid import uuid4

import httpx

try:
    from src.settings import get_settings
except ModuleNotFoundError:
    from backend_v2.src.settings import get_settings


class DnseMarketDataConfigError(RuntimeError):
    """Raised when DNSE market data credentials are missing."""


def build_signature(
    *,
    secret: str,
    method: str,
    path: str,
    date_value: str,
    algorithm: str = "hmac-sha256",
    nonce: str | None = None,
    header_name: str = "Date",
) -> tuple[str, str]:
    header_key = header_name.lower()
    headers = f"(request-target) {header_key}"
    signature_string = f"(request-target): {method.lower()} {path}\n{header_key}: {date_value}"
    if nonce:
        signature_string += f"\nnonce: {nonce}"

    digestmod = {
        "hmac-sha256": hashlib.sha256,
        "hmac-sha384": hashlib.sha384,
        "hmac-sha512": hashlib.sha512,
    }.get(algorithm, hashlib.sha1)
    mac = hmac.new(secret.encode("utf-8"), signature_string.encode("utf-8"), digestmod)
    encoded = base64.b64encode(mac.digest()).decode("utf-8")
    return headers, parse.quote(encoded, safe="")


def _first_number(raw: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = raw.get(key)
        if value is None or value == "":
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _first_text(raw: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = raw.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


def normalize_latest_trade(symbol: str, raw: dict[str, Any]) -> dict[str, Any]:
    trade = raw
    wrapped_trades = raw.get("trades")
    if isinstance(wrapped_trades, list) and wrapped_trades and isinstance(wrapped_trades[0], dict):
        trade = wrapped_trades[0]

    price = _first_number(trade, ("price", "matchedPrice", "lastPrice", "matchPrice", "p"))
    volume = _first_number(trade, ("volume", "matchedVolume", "matchVolume", "matchQtty", "vol", "v"))
    trade_time = _first_text(trade, ("time", "tradeTime", "tradingTime", "createdAt", "t"))
    return {
        "symbol": symbol.strip().upper(),
        "price": price,
        "volume": int(volume) if volume is not None else None,
        "trade_time": trade_time,
        "source": "dnse",
        "raw": raw,
    }


class DnseMarketDataClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
        board_id: str | None = None,
        timeout_seconds: float = 10.0,
    ):
        settings = get_settings()
        self.api_key = (api_key if api_key is not None else settings.dnse_market_api_key).strip()
        self.api_secret = (api_secret if api_secret is not None else settings.dnse_market_api_secret).strip()
        self.base_url = (base_url or settings.dnse_market_base_url).rstrip("/")
        self.board_id = (board_id if board_id is not None else settings.dnse_market_board_id).strip()
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def latest_trade_url(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        path = f"/price/{parse.quote(normalized, safe='')}/trades/latest"
        query = {"boardId": self.board_id} if self.board_id else None
        if query:
            return f"{self.base_url}{path}?{parse.urlencode(query)}"
        return f"{self.base_url}{path}"

    def build_headers(self, method: str, path: str) -> dict[str, str]:
        if not self.is_configured:
            raise DnseMarketDataConfigError("DNSE market data credentials are not configured.")

        date_value = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
        nonce = uuid4().hex
        headers_list, signature = build_signature(
            secret=self.api_secret,
            method=method,
            path=path,
            date_value=date_value,
            nonce=nonce,
        )
        signature_header = (
            f'Signature keyId="{self.api_key}",algorithm="hmac-sha256",'
            f'headers="{headers_list}",signature="{signature}",nonce="{nonce}"'
        )
        return {
            "Date": date_value,
            "X-Signature": signature_header,
            "x-api-key": self.api_key,
        }

    async def get_latest_trade(self, symbol: str) -> dict[str, Any]:
        normalized = symbol.strip().upper()
        path = f"/price/{parse.quote(normalized, safe='')}/trades/latest"
        url = self.latest_trade_url(normalized)
        headers = self.build_headers("GET", path)
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url, headers=headers)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        response.raise_for_status()
        raw = response.json()
        if not isinstance(raw, dict):
            raw = {"data": raw}
        tick = normalize_latest_trade(normalized, raw)
        tick["latency_ms"] = latency_ms
        return tick

    async def get_latest_trades(self, symbols: list[str]) -> dict[str, Any]:
        ticks: list[dict[str, Any]] = []
        errors: dict[str, str] = {}
        started = time.perf_counter()
        for symbol in symbols:
            normalized = symbol.strip().upper()
            if not normalized:
                continue
            try:
                ticks.append(await self.get_latest_trade(normalized))
            except Exception as exc:
                errors[normalized] = str(exc)

        return {
            "status": "ok" if ticks else "error",
            "source": "dnse",
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "symbols": [symbol.strip().upper() for symbol in symbols if symbol.strip()],
            "ticks": ticks,
            "errors": errors,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }


def get_dnse_market_client() -> DnseMarketDataClient:
    return DnseMarketDataClient()
