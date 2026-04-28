"""Processed parquet writer with symbol partitions and metadata."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from etl.config import EtlConfig
from etl.logging_setup import get_logger

log = get_logger(__name__)


def _file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_processed_parquet(dataset: pd.DataFrame, cfg: EtlConfig) -> Path:
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    out = cfg.processed_dir / f"market_data_{cfg.run_id}.parquet"
    dataset.to_parquet(out, index=False)

    by_symbol_dir = cfg.processed_dir / "by_symbol"
    if "symbol" in dataset.columns:
        for symbol, frame in dataset.groupby("symbol"):
            symbol_dir = by_symbol_dir / str(symbol).upper()
            symbol_dir.mkdir(parents=True, exist_ok=True)
            frame.to_parquet(symbol_dir / "latest.parquet", index=False)

    missing_counts = dataset.isna().sum().sort_values(ascending=False)
    quality_summary = {
        "outlier_count": int(dataset["is_outlier"].fillna(False).sum()) if "is_outlier" in dataset.columns else 0,
        "duplicate_rows": int(dataset.duplicated().sum()),
        "columns_with_missing": int((missing_counts > 0).sum()),
        "top_missing_columns": {
            str(column): int(count)
            for column, count in missing_counts[missing_counts > 0].head(10).items()
        },
    }

    metadata = {
        "run_id": cfg.run_id,
        "row_count": int(len(dataset)),
        "columns": list(dataset.columns),
        "date_range": {
            "min": str(dataset["data_date"].min()) if "data_date" in dataset.columns and not dataset.empty else None,
            "max": str(dataset["data_date"].max()) if "data_date" in dataset.columns and not dataset.empty else None,
        },
        "symbols": sorted(dataset["symbol"].dropna().unique().tolist()) if "symbol" in dataset.columns else [],
        "schema_version": 2,
        "quality_summary": quality_summary,
        "checksum_sha256": _file_checksum(out),
    }
    meta_path = cfg.processed_dir / f"market_data_{cfg.run_id}.meta.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("Saved processed parquet %s rows=%d metadata=%s", out, len(dataset), meta_path)
    return out


def cleanup_old_snapshots(cfg: EtlConfig, keep: int = 5) -> int:
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(cfg.processed_dir.glob("market_data_*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)
    stale = files[max(keep, 0):]
    deleted = 0
    for parquet_path in stale:
        stem = parquet_path.with_suffix("")
        meta_path = stem.with_suffix(".meta.json")
        csv_path = stem.with_suffix(".csv")
        for path in (parquet_path, meta_path, csv_path):
            if path.exists():
                path.unlink()
                deleted += 1
    if deleted:
        log.info("Cleaned up %d old processed snapshot files", deleted)
    return deleted
