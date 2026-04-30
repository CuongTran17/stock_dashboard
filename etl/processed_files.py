from __future__ import annotations

from pathlib import Path


def latest_processed_parquet(processed_dir: Path, *, exclude_run_id: str | None = None) -> Path | None:
    files = sorted(
        (
            path
            for path in processed_dir.glob("market_data_*.parquet")
            if exclude_run_id is None or exclude_run_id not in path.name
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None
