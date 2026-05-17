import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

from etl.config import EtlConfig
from etl.run_etl import _resolve_incremental_cfg


class IncrementalConfigTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
