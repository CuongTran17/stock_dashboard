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


class StockReadApiSnapshotModeTests(unittest.IsolatedAsyncioTestCase):
    async def test_snapshot_refresh_param_is_rejected(self):
        from src.routes.stocks import get_snapshots

        with self.assertRaises(HTTPException) as ctx:
            await get_snapshots(symbols="FPT", refresh=True)

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail["code"], "REFRESH_DISABLED_IN_SNAPSHOT_MODE")

    async def test_history_does_not_auto_fetch_when_db_empty(self):
        from src.routes import stocks

        async def empty_history(*args, **kwargs):
            return []

        async def forbidden_refresh(*args, **kwargs):
            raise AssertionError("read API attempted to create market data")

        original_load = stocks.fetcher_service.load_history_from_db_async
        original_refresh = stocks.fetcher_service.refresh_history_for_symbol
        stocks.fetcher_service.load_history_from_db_async = empty_history
        stocks.fetcher_service.refresh_history_for_symbol = forbidden_refresh
        try:
            result = await stocks.get_history("FPT", limit=30)
        finally:
            stocks.fetcher_service.load_history_from_db_async = original_load
            stocks.fetcher_service.refresh_history_for_symbol = original_refresh

        self.assertEqual(result["data_status"], "NO_DATA_IN_SNAPSHOT")
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["data"], [])


class MarketAndInternalSnapshotModeTests(unittest.IsolatedAsyncioTestCase):
    async def test_market_indices_refresh_is_rejected(self):
        from src.routes.market import get_market_indices

        with self.assertRaises(HTTPException) as ctx:
            await get_market_indices(refresh=True)

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail["code"], "REFRESH_DISABLED_IN_SNAPSHOT_MODE")

    async def test_debug_intraday_refresh_is_rejected(self):
        from src.routes.internal import debug_refresh_intraday

        with self.assertRaises(HTTPException) as ctx:
            await debug_refresh_intraday(symbols="FPT")

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail["code"], "REFRESH_DISABLED_IN_SNAPSHOT_MODE")


if __name__ == "__main__":
    unittest.main()
