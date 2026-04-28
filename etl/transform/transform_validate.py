"""Data-quality helpers for the transform layer."""
from __future__ import annotations

from typing import Mapping

import pandas as pd

from etl.logging_setup import get_logger

log = get_logger(__name__)


def _detect_price_outliers(df: pd.DataFrame, price_col: str = "close_price") -> pd.Series:
    if df.empty or price_col not in df.columns:
        return pd.Series(False, index=df.index, dtype=bool)

    price = pd.to_numeric(df[price_col], errors="coerce")
    if price.notna().sum() < 8:
        return pd.Series(False, index=df.index, dtype=bool)

    q1 = price.quantile(0.25)
    q3 = price.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or iqr <= 0:
        return pd.Series(False, index=df.index, dtype=bool)

    lower = q1 - 3 * iqr
    upper = q3 + 3 * iqr
    return ((price < lower) | (price > upper)).fillna(False)


def validate_and_clean(df: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
    """Drop invalid critical rows, deduplicate, and flag price outliers."""
    if df.empty:
        out = df.copy()
        out["is_outlier"] = pd.Series(dtype=bool)
        return out

    out = df.copy()
    start_rows = len(out)
    out["close_price"] = pd.to_numeric(out.get("close_price"), errors="coerce")
    out = out[out["close_price"].notna() & (out["close_price"] > 0)]

    if "data_date" in out.columns:
        out["data_date"] = pd.to_datetime(out["data_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        out = out[out["data_date"].notna()]

    dedupe_cols = [c for c in ("symbol", "data_date") if c in out.columns]
    duplicate_count = 0
    if dedupe_cols:
        duplicate_count = int(out.duplicated(dedupe_cols, keep="last").sum())
        out = out.drop_duplicates(dedupe_cols, keep="last")

    out = out.sort_values("data_date").reset_index(drop=True) if "data_date" in out.columns else out.reset_index(drop=True)
    out["is_outlier"] = _detect_price_outliers(out)

    outlier_count = int(out["is_outlier"].sum())
    dropped = start_rows - len(out)
    if dropped or duplicate_count or outlier_count:
        log.warning(
            "Quality clean %s dropped=%d duplicates=%d outliers=%d",
            symbol or "-",
            dropped,
            duplicate_count,
            outlier_count,
        )
    return out


def enforce_schema(df: pd.DataFrame, expected_dtypes: Mapping[str, str]) -> pd.DataFrame:
    """Ensure expected columns exist and cast known dtypes best-effort."""
    out = df.copy()
    for col, dtype in expected_dtypes.items():
        if col not in out.columns:
            out[col] = pd.NA
        try:
            if dtype.startswith("float"):
                out[col] = pd.to_numeric(out[col], errors="coerce").astype(dtype)
            elif dtype.startswith("int"):
                out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(dtype)
            elif dtype == "bool":
                out[col] = out[col].fillna(False).astype(bool)
            elif dtype in {"str", "string"}:
                out[col] = out[col].fillna("").astype(str)
            else:
                out[col] = out[col].astype(dtype)
        except (TypeError, ValueError):
            log.warning("Could not cast column %s to %s", col, dtype)
    return out


def report_quality_metrics(df: pd.DataFrame, symbol: str) -> dict[str, object]:
    if df.empty:
        metrics = {"symbol": symbol, "rows": 0, "nan_ratio": {}, "gap_days": 0, "outliers": 0}
        log.info("Quality metrics %s %s", symbol, metrics)
        return metrics

    dates = pd.to_datetime(df.get("data_date"), errors="coerce").dropna().sort_values()
    gap_days = 0
    if not dates.empty:
        expected = pd.bdate_range(dates.min(), dates.max())
        actual = pd.DatetimeIndex(dates.dt.normalize().unique())
        gap_days = max(len(expected.difference(actual)), 0)

    nan_ratio = {
        col: round(float(df[col].isna().mean()), 4)
        for col in df.columns
        if df[col].isna().any()
    }
    metrics = {
        "symbol": symbol,
        "rows": int(len(df)),
        "nan_ratio": nan_ratio,
        "gap_days": int(gap_days),
        "outliers": int(df.get("is_outlier", pd.Series(dtype=bool)).fillna(False).sum()),
    }
    log.info(
        "Quality metrics %s rows=%d gap_days=%d outliers=%d",
        symbol,
        metrics["rows"],
        gap_days,
        metrics["outliers"],
    )
    return metrics
