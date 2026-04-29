"""
Analysis routes – /api/analysis/*

Provides the AI-powered stock analysis endpoint backed by the Kaggle Trading-R1 model.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.cache import _load_technical_cache
from src.database.db import AsyncSessionLocal
from src.database.models import AIPrediction
from src.routes.stocks import _ensure_history_data
from src.services.fundamental_fetcher import fundamental_service
from src.services.vnstock_fetcher import VN30_SYMBOLS, fetcher_service
from src.settings import get_settings
from src.utils import _extract_valuation_from_ratios, _to_float

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analysis"])
settings = get_settings()


# ── Helper functions ──────────────────────────────────────────────────


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
        tail = re.split(
            r"\n\s*(?:FINAL DECISION|CONFIDENCE|<\/think>|<\|think\|>)",
            tail,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        for line in tail.splitlines():
            candidate = line.strip()
            candidate = re.sub(r"^[\-\*\d\.\)\s]+", "", candidate)
            if candidate:
                factors.append(candidate)

    return list(dict.fromkeys(factors))


# ── Route ─────────────────────────────────────────────────────────────


@router.post("/api/analysis/{symbol}/generate")
async def generate_analysis(
    symbol: str,
    user_id: Optional[int] = Query(default=None, description="User ID (optional)"),
    force: bool = Query(default=False, description="Force refresh from Kaggle model"),
) -> dict[str, Any]:
    """Call Kaggle Trading-R1 model to generate analysis for a stock symbol with rich data."""

    symbol = symbol.upper()
    if symbol not in VN30_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not in VN30 list")

    kaggle_api_url = settings.kaggle_api_url.strip()
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
            cached_row, tech_payload = await _load_technical_cache(
                symbol,
                start_date=None,
                end_date=None,
                limit=365,
            )

            if tech_payload and isinstance(tech_payload, dict):
                indicators = tech_payload.get("indicators", {})

                sma7 = indicators.get("sma_7")
                sma21 = indicators.get("sma_21")
                rsi = indicators.get("rsi_14")
                macd = indicators.get("macd")
                signal = indicators.get("signal")

                if isinstance(rsi, list) and len(rsi) > 0:
                    rsi = rsi[-1]
                if isinstance(macd, list) and len(macd) > 0:
                    macd = macd[-1]
                if isinstance(signal, list) and len(signal) > 0:
                    signal = signal[-1]

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
            logger.warning("Could not load technical data for %s: %s", symbol, e)
            technical_info = "TECHNICAL ANALYSIS: Limited indicator data (exception)"

        # 3 & 4. Fetch fundamentals and news in parallel
        overview_data = "FUNDAMENTALS: Not available"
        news_data = "RECENT NEWS: Not available"
        try:
            (overview_payload, _), (ratio_records, _), (news_list, _) = await asyncio.gather(
                fundamental_service.refresh_company_overview(symbol),
                fundamental_service.refresh_financial_report(symbol, "ratios"),
                fundamental_service.get_symbol_news(symbol, refresh=False),
            )

            profile = overview_payload if isinstance(overview_payload, dict) else {}
            valuation = _extract_valuation_from_ratios(ratio_records or [])
            company_profile = profile.get("company_profile")
            company_name = profile.get("company_name", profile.get("companyName", symbol))
            industry = profile.get("industry", "N/A")
            overview_data = (
                f"FUNDAMENTALS:\n"
                f"- Company: {company_name}\n"
                f"- Industry: {industry}\n"
                f"- P/E Ratio: {valuation.get('pe', 'N/A')}\n"
                f"- P/B Ratio: {valuation.get('pb', 'N/A')}\n"
                f"- EPS: {valuation.get('eps', 'N/A')}\n"
                f"- ROE: {valuation.get('roe', 'N/A')}\n"
                f"- ROA: {valuation.get('roa', 'N/A')}\n"
                f"- Market Cap: {valuation.get('market_cap', profile.get('market_cap', 'N/A'))}\n"
                f"- Profile Summary: {str(company_profile)[:300] if company_profile else 'N/A'}"
            )

            if news_list:
                news_items = "\n".join(
                    f"- {n.get('title', 'N/A')} ({n.get('publish_time', n.get('time', 'N/A'))})"
                    for n in news_list[:3]
                )
                news_data = f"RECENT NEWS:\n{news_items}"
        except Exception as e:
            logger.warning("Could not load fundamentals/news for %s: %s", symbol, e)

        logger.info(
            "[ANALYSIS_CONTEXT] fundamentals=%s | news=%s",
            overview_data.replace("\n", " | "),
            news_data.replace("\n", " | "),
        )

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

        logger.debug("[PROMPT_DEBUG] Sending prompt to Kaggle:\n%s\n---END PROMPT---", user_prompt)

        # 6. Call Kaggle Trading-R1 model
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{kaggle_api_url}/api/analyze",
                json={"prompt": user_prompt},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                logger.error("Kaggle API error: %s - %s", response.status_code, response.text)
                raise HTTPException(status_code=503, detail=f"Kaggle API error: {response.status_code}")

            analysis_result = response.json()

        # 7. Parse Kaggle response
        decision = analysis_result.get("decision", "HOLD").upper()
        confidence = float(analysis_result.get("confidence", 50))
        if confidence > 1:
            confidence = confidence / 100.0
        reasoning = analysis_result.get("conclusion", analysis_result.get("reasoning", ""))
        raw_output = _extract_kaggle_output_text(analysis_result)
        key_factors = _extract_kaggle_key_factors(raw_output)
        if not reasoning and raw_output:
            reasoning = raw_output

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
                model_version="Trading-R1/Qwen3.5-2B",
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
                "data_source": "MySQL (history) + vnstock (live) + Kaggle Trading-R1 (analysis)",
            },
            "model_version": "Trading-R1/Qwen3.5-2B",
        }

    except StarletteHTTPException:
        raise
    except httpx.RequestError as exc:
        logger.error("Kaggle API connection error: %s", exc)
        raise HTTPException(status_code=503, detail=f"Kaggle API connection error: {exc}")
    except Exception as exc:
        logger.error("Analysis generation error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Analysis error: {exc}")
