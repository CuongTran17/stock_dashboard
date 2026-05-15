from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import duckdb

try:
    from src.settings import REPO_ROOT, get_settings
except ModuleNotFoundError:
    from backend_v2.src.settings import REPO_ROOT, get_settings


def _resolve_duckdb_path(path_value: str | Path | None = None) -> Path:
    raw = Path(path_value or get_settings().duckdb_path)
    return raw if raw.is_absolute() else REPO_ROOT / raw


def _to_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def _optional_date(value: Any) -> date | None:
    if value is None:
        return None
    return _to_date(value)


@dataclass(frozen=True)
class TechnicalCacheRow:
    symbol: str
    start_date: date | None
    end_date: date | None
    limit_value: int
    history_count: int
    history_last_time: str | None
    payload_json: str
    source: str
    updated_at: datetime


class MarketDuckDB:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = _resolve_duckdb_path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def ensure_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_ohlcv (
                    symbol VARCHAR NOT NULL,
                    date DATE NOT NULL,
                    open DOUBLE NOT NULL DEFAULT 0,
                    high DOUBLE NOT NULL DEFAULT 0,
                    low DOUBLE NOT NULL DEFAULT 0,
                    close DOUBLE NOT NULL DEFAULT 0,
                    volume BIGINT NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (symbol, date)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS technical_cache (
                    symbol VARCHAR NOT NULL,
                    start_date DATE,
                    end_date DATE,
                    limit_value INTEGER NOT NULL DEFAULT 365,
                    history_count INTEGER NOT NULL DEFAULT 0,
                    history_last_time VARCHAR,
                    payload_json VARCHAR NOT NULL,
                    source VARCHAR NOT NULL DEFAULT 'duckdb',
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def upsert_daily_rows(self, symbol: str, rows: Iterable[dict[str, Any]]) -> int:
        normalized = symbol.strip().upper()
        payload = [
            (
                normalized,
                _to_date(row["date"]),
                float(row.get("open") or 0),
                float(row.get("high") or 0),
                float(row.get("low") or 0),
                float(row.get("close") or 0),
                int(float(row.get("volume") or 0)),
                datetime.now(timezone.utc).replace(tzinfo=None),
            )
            for row in rows
        ]
        if not payload:
            return 0

        with self.connect() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                conn.executemany(
                    "DELETE FROM daily_ohlcv WHERE symbol = ? AND date = ?",
                    [(item[0], item[1]) for item in payload],
                )
                conn.executemany(
                    """
                    INSERT INTO daily_ohlcv
                        (symbol, date, open, high, low, close, volume, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[7])
                        for item in payload
                    ],
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        return len(payload)

    def load_history(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 365,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT date, open, high, low, close, volume
            FROM daily_ohlcv
            WHERE symbol = ?
        """
        params: list[Any] = [symbol.strip().upper()]
        if start_date is not None:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date is not None:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date DESC LIMIT ?"
        params.append(max(limit, 1))

        with self.connect() as conn:
            records = conn.execute(query, params).fetchall()

        rows = list(reversed(records))
        return [
            {
                "time": item[0].isoformat(),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": int(item[5]),
            }
            for item in rows
        ]

    @staticmethod
    def _technical_where_clause(start_date: date | None, end_date: date | None) -> tuple[str, list[Any]]:
        clauses = ["symbol = ?", "limit_value = ?"]
        params: list[Any] = []
        if start_date is None:
            clauses.append("start_date IS NULL")
        else:
            clauses.append("start_date = ?")
            params.append(start_date)
        if end_date is None:
            clauses.append("end_date IS NULL")
        else:
            clauses.append("end_date = ?")
            params.append(end_date)
        return " AND ".join(clauses), params

    def upsert_technical_cache(
        self,
        symbol: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
        history_count: int,
        history_last_time: str | None,
        payload: dict[str, Any],
        source: str = "duckdb",
    ) -> str:
        normalized = symbol.strip().upper()
        safe_start = _optional_date(start_date)
        safe_end = _optional_date(end_date)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        payload_json = json.dumps(payload, ensure_ascii=False, default=str)
        where_sql, date_params = self._technical_where_clause(safe_start, safe_end)

        with self.connect() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                conn.execute(
                    f"DELETE FROM technical_cache WHERE {where_sql}",
                    [normalized, int(limit), *date_params],
                )
                conn.execute(
                    """
                    INSERT INTO technical_cache
                        (symbol, start_date, end_date, limit_value, history_count, history_last_time, payload_json, source, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        normalized,
                        safe_start,
                        safe_end,
                        int(limit),
                        int(history_count),
                        history_last_time,
                        payload_json,
                        source,
                        now,
                    ],
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        return now.replace(tzinfo=timezone.utc).isoformat()

    def load_technical_cache(
        self,
        symbol: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
    ) -> tuple[TechnicalCacheRow | None, dict[str, Any] | None]:
        normalized = symbol.strip().upper()
        safe_start = _optional_date(start_date)
        safe_end = _optional_date(end_date)
        where_sql, date_params = self._technical_where_clause(safe_start, safe_end)

        with self.connect() as conn:
            record = conn.execute(
                f"""
                SELECT symbol, start_date, end_date, limit_value, history_count, history_last_time, payload_json, source, updated_at
                FROM technical_cache
                WHERE {where_sql}
                LIMIT 1
                """,
                [normalized, int(limit), *date_params],
            ).fetchone()

        if record is None:
            return None, None

        updated_at = record[8]
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        row = TechnicalCacheRow(
            symbol=record[0],
            start_date=record[1],
            end_date=record[2],
            limit_value=int(record[3]),
            history_count=int(record[4]),
            history_last_time=record[5],
            payload_json=record[6],
            source=record[7],
            updated_at=updated_at,
        )
        payload = json.loads(row.payload_json)
        return row, payload if isinstance(payload, dict) else {}


class LazyMarketDuckDB:
    def __init__(self):
        self._repo: MarketDuckDB | None = None

    def _get_repo(self) -> MarketDuckDB:
        if self._repo is None:
            self._repo = MarketDuckDB()
        return self._repo

    def upsert_daily_rows(self, symbol: str, rows: Iterable[dict[str, Any]]) -> int:
        return self._get_repo().upsert_daily_rows(symbol, rows)

    def load_history(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 365,
    ) -> list[dict[str, Any]]:
        return self._get_repo().load_history(symbol, start_date=start_date, end_date=end_date, limit=limit)

    def upsert_technical_cache(
        self,
        symbol: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
        history_count: int,
        history_last_time: str | None,
        payload: dict[str, Any],
        source: str = "duckdb",
    ) -> str:
        return self._get_repo().upsert_technical_cache(
            symbol,
            start_date,
            end_date,
            limit,
            history_count,
            history_last_time,
            payload,
            source,
        )

    def load_technical_cache(
        self,
        symbol: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
    ) -> tuple[TechnicalCacheRow | None, dict[str, Any] | None]:
        return self._get_repo().load_technical_cache(symbol, start_date, end_date, limit)


market_repo = LazyMarketDuckDB()
