"""Tính toán chỉ báo kỹ thuật (SMA, EMA, RSI, MACD).

Các hàm trong module này **không biết** về warm-up: chúng chỉ tính trên
chuỗi đầu vào. Việc lùi ``fetch_start`` và cắt lại về ``user_start`` được
thực hiện ở ``build_dataset``.
"""
from __future__ import annotations

import pandas as pd


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def add_price_indicators(df: pd.DataFrame, close_col: str = "close_price") -> pd.DataFrame:
    """Thêm SMA7, EMA21, RSI14, MACD(12,26) vào ``df`` (đã sort theo ngày)."""
    if df.empty or close_col not in df.columns:
        return df

    out = df.copy()
    close = out[close_col]

    out["sma_7"] = close.rolling(window=7, min_periods=7).mean()
    out["ema_21"] = close.ewm(span=21, adjust=False).mean()
    out["rsi_14"] = calculate_rsi(close, period=14)

    ema_fast = close.ewm(span=12, adjust=False).mean()
    ema_slow = close.ewm(span=26, adjust=False).mean()
    out["macd"] = ema_fast - ema_slow

    return out
