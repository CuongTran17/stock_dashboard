import unittest

from fastapi import HTTPException

from src.market_data_status import (
    DATA_AVAILABLE,
    REFRESH_DISABLED_IN_SNAPSHOT_MODE,
    MarketDataStatus,
    market_meta,
    reject_refresh_in_snapshot_mode,
)


class MarketDataStatusTests(unittest.TestCase):
    def test_status_constants_are_stable_strings(self):
        self.assertEqual(DATA_AVAILABLE, "DATA_AVAILABLE")
        self.assertEqual(REFRESH_DISABLED_IN_SNAPSHOT_MODE, "REFRESH_DISABLED_IN_SNAPSHOT_MODE")
        self.assertEqual(MarketDataStatus.STALE_SNAPSHOT, "STALE_SNAPSHOT")

    def test_market_meta_uses_stable_shape(self):
        meta = market_meta(
            DATA_AVAILABLE,
            run_id="20260514T230000",
            last_synced_at="2026-05-14T16:00:00+00:00",
            stale=True,
            message="Loaded from MySQL serving cache",
        )

        self.assertEqual(
            meta,
            {
                "data_status": "DATA_AVAILABLE",
                "run_id": "20260514T230000",
                "last_synced_at": "2026-05-14T16:00:00+00:00",
                "stale": True,
                "message": "Loaded from MySQL serving cache",
            },
        )

    def test_reject_refresh_raises_http_409(self):
        with self.assertRaises(HTTPException) as ctx:
            reject_refresh_in_snapshot_mode(True)

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail["code"], "REFRESH_DISABLED_IN_SNAPSHOT_MODE")

    def test_reject_refresh_allows_false(self):
        self.assertIsNone(reject_refresh_in_snapshot_mode(False))


class ReadOnlyLifespanTests(unittest.IsolatedAsyncioTestCase):
    async def test_lifespan_initializes_db_without_market_background_work(self):
        from src.jobs import build_lifespan

        calls = []

        def init_db():
            calls.append("init_db")

        class App:
            pass

        lifespan = build_lifespan(init_db=init_db)
        async with lifespan(App()):
            calls.append("inside")

        self.assertEqual(calls, ["init_db", "inside"])


if __name__ == "__main__":
    unittest.main()
