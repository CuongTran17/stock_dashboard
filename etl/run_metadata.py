"""Run metadata tracking for ETL executions."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from etl.config import EtlConfig


@dataclass
class RunMetadata:
    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "running"
    symbols: list[str] = field(default_factory=list)
    row_count: int = 0
    errors: dict[str, str] = field(default_factory=dict)
    duration_seconds: float = 0.0
    output_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["started_at"] = self.started_at.isoformat()
        data["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        return data


def _runs_dir(cfg: EtlConfig) -> Path:
    path = cfg.processed_dir / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_run_metadata(metadata: RunMetadata, cfg: EtlConfig) -> Path:
    path = _runs_dir(cfg) / f"{metadata.run_id}.json"
    path.write_text(json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_run_metadata(path: Path) -> RunMetadata | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return RunMetadata(
            run_id=str(raw.get("run_id") or path.stem),
            started_at=datetime.fromisoformat(raw["started_at"]),
            completed_at=datetime.fromisoformat(raw["completed_at"]) if raw.get("completed_at") else None,
            status=str(raw.get("status") or "unknown"),
            symbols=list(raw.get("symbols") or []),
            row_count=int(raw.get("row_count") or 0),
            errors=dict(raw.get("errors") or {}),
            duration_seconds=float(raw.get("duration_seconds") or 0.0),
            output_file=raw.get("output_file"),
        )
    except Exception:
        return None


def load_recent_runs(cfg: EtlConfig, limit: int = 10) -> list[RunMetadata]:
    runs_dir = cfg.processed_dir / "runs"
    if not runs_dir.exists():
        return []
    items = [item for item in (load_run_metadata(path) for path in runs_dir.glob("*.json")) if item is not None]
    items.sort(key=lambda item: item.started_at, reverse=True)
    return items[:limit]


def running_metadata(cfg: EtlConfig) -> RunMetadata:
    return RunMetadata(
        run_id=cfg.run_id,
        started_at=datetime.now(timezone.utc),
        symbols=list(cfg.symbols),
    )


def complete_metadata(
    metadata: RunMetadata,
    *,
    status: str,
    row_count: int = 0,
    output_file: str | None = None,
    errors: dict[str, str] | None = None,
) -> RunMetadata:
    completed = datetime.now(timezone.utc)
    metadata.completed_at = completed
    metadata.status = status
    metadata.row_count = row_count
    metadata.output_file = output_file
    metadata.errors = errors or {}
    metadata.duration_seconds = (completed - metadata.started_at).total_seconds()
    return metadata
