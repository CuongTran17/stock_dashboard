import tempfile
import unittest
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from etl.config import EtlConfig
from etl.backfill_dnse_ticks import backfill_dnse_ticks_for_session
from etl.run_etl import _build_argparser, _resolve_incremental_cfg


class IncrementalConfigTests(unittest.TestCase):
    def test_cli_default_end_date_uses_today(self):
        parsed = _build_argparser().parse_args([])

        self.assertEqual(parsed.end_date, date.today().isoformat())

    def test_resolves_incremental_start_from_latest_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            lake_dir = Path(tmp) / "lake"
            processed_dir = lake_dir / "processed"
            processed_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "symbol": ["FPT", "VCB"],
                    "data_date": ["2026-05-10", "2026-05-12"],
                }
            ).to_parquet(processed_dir / "market_data_20260512T150000.parquet", index=False)

            cfg = EtlConfig.from_args(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 5, 15),
                symbols=["FPT", "VCB"],
                lake_dir=lake_dir,
                run_mode="incremental",
                incremental_overlap_days=7,
            )

            resolved = _resolve_incremental_cfg(cfg)

        self.assertEqual(resolved.user_start, date(2026, 5, 5))
        self.assertEqual(resolved.user_end, date(2026, 5, 15))


@dataclass
class FakeDnseTickClient:
    calls: list[str]

    async def get_historical_trades_for_session(self, symbol: str, session_date: date):
        self.calls.append(symbol)
        return [
            {
                "id": f"dnse-historical|{symbol}|2026-06-08T09:01:00+07:00|100.0|10",
                "symbol": symbol,
                "time": "2026-06-08T09:01:00+07:00",
                "price": 100.0,
                "volume": 10,
                "match_type": "buy",
                "side_source": "dnse",
                "side_confidence": "source",
                "source": "dnse_historical",
            }
        ]


class DnseTickBackfillTests(unittest.TestCase):
    def test_backfill_skips_existing_symbol_and_fetches_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            existing = base_dir / "2026-06-08"
            existing.mkdir(parents=True)
            pd.DataFrame(
                [
                    {
                        "symbol": "FPT",
                        "time": "2026-06-08T09:01:00+07:00",
                        "price": 100.0,
                        "volume": 10,
                        "source": "dnse_historical",
                    }
                ]
            ).to_parquet(existing / "FPT.parquet", index=False)
            client = FakeDnseTickClient(calls=[])

            result = backfill_dnse_ticks_for_session(
                ["FPT", "VCB"],
                date(2026, 6, 8),
                base_dir=base_dir,
                client=client,
            )

            self.assertEqual(result.session_date, date(2026, 6, 8))
            self.assertEqual(result.skipped_existing, ["FPT"])
            self.assertEqual(result.backfilled, ["VCB"])
            self.assertEqual(result.failed, {})
            self.assertEqual(client.calls, ["VCB"])
            self.assertTrue((base_dir / "2026-06-08" / "VCB.parquet").exists())

    def test_backfill_refetches_existing_realtime_cache_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            existing = base_dir / "2026-06-08"
            existing.mkdir(parents=True)
            pd.DataFrame(
                [
                    {
                        "symbol": "FPT",
                        "time": "2026-06-08T14:45:00+07:00",
                        "price": 100.0,
                        "volume": 10,
                    }
                ]
            ).to_parquet(existing / "FPT.parquet", index=False)
            client = FakeDnseTickClient(calls=[])

            result = backfill_dnse_ticks_for_session(
                ["FPT"],
                date(2026, 6, 8),
                base_dir=base_dir,
                client=client,
            )

            self.assertEqual(result.skipped_existing, [])
            self.assertEqual(result.backfilled, ["FPT"])
            self.assertEqual(client.calls, ["FPT"])
            refreshed = pd.read_parquet(existing / "FPT.parquet")
            self.assertEqual(set(refreshed["source"]), {"dnse_historical"})


if __name__ == "__main__":
    unittest.main()
