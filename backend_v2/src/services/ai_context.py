from __future__ import annotations

import json
from typing import Any


AI_FEATURE_COLUMNS = [
    "symbol",
    "data_date",
    "close_price",
    "volume",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_histogram",
    "sma_7",
    "ema_21",
    "vol_sma_20",
    "atr_14",
    "micro_pe",
    "micro_pb",
    "micro_roe",
    "micro_roa",
    "micro_eps",
    "micro_de",
    "fund_revenue_growth",
    "macro_vnindex_close",
    "macro_vn30_close",
    "news_headlines",
    "event_headlines",
    "google_news_headlines",
    "run_id",
]


def select_market_feature_context(symbol: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError(f"No market feature rows found for {symbol}")
    latest = sorted(rows, key=lambda item: str(item.get("data_date") or ""))[-1]
    context = dict(latest)
    context["symbol"] = symbol.strip().upper()
    context["market_feature_run_id"] = context.get("run_id")
    return context


def build_prompt(context: dict[str, Any], prompt_version: str = "vn30-v1") -> str:
    symbol = str(context.get("symbol") or "").upper()
    context_json = json.dumps(context, ensure_ascii=False, default=str, sort_keys=True)
    return f"""
ANALYZE {symbol} STOCK

PROMPT_VERSION: {prompt_version}

MARKET_CONTEXT_JSON:
{context_json}

TASK:
Return JSON only with this schema:
{{
  "decision": "BUY | SELL | HOLD",
  "confidence": 0-100,
  "conclusion": "short reasoning",
  "key_factors": ["factor 1", "factor 2"]
}}
""".strip()


async def build_analysis_context(
    symbol: str,
    repo: Any,
    news_loader: Any = None,
    overview_loader: Any = None,
) -> dict[str, Any]:
    rows = repo.load_market_features(symbols=[symbol], columns=AI_FEATURE_COLUMNS, limit=365)
    context = select_market_feature_context(symbol, rows)
    if news_loader is not None:
        context["news"] = await news_loader(symbol)
    if overview_loader is not None:
        context["overview"] = await overview_loader(symbol)
    return context
