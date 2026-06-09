import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from fastapi import HTTPException
import pandas as pd

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


class SmallRuntimeModeSettingsTests(unittest.TestCase):
    def test_backend_defaults_to_no_request_duckdb_writes_and_no_startup_etl(self):
        from src.settings import Settings

        settings = Settings()

        self.assertFalse(settings.duckdb_request_reads_enabled)
        self.assertFalse(settings.duckdb_request_writes_enabled)
        self.assertFalse(settings.etl_run_on_backend_start)


class TechnicalCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_load_technical_cache_skips_duckdb_when_request_reads_disabled(self):
        from src import cache

        calls = []

        class ForbiddenMarketRepo:
            def load_technical_cache(self, *args, **kwargs):
                calls.append("read")
                raise AssertionError("DuckDB read should be skipped")

        original_repo = cache.market_repo
        cache.market_repo = ForbiddenMarketRepo()
        try:
            row, payload = await cache._load_technical_cache("FPT", None, None, 180)
        finally:
            cache.market_repo = original_repo

        self.assertIsNone(row)
        self.assertIsNone(payload)
        self.assertEqual(calls, [])

    async def test_load_technical_cache_returns_empty_when_duckdb_is_unavailable(self):
        from src import cache

        class UnavailableMarketRepo:
            def load_technical_cache(self, *args, **kwargs):
                raise OSError("duckdb locked")

        original_repo = cache.market_repo
        cache.market_repo = UnavailableMarketRepo()
        try:
            row, payload = await cache._load_technical_cache("FPT", None, None, 180)
        finally:
            cache.market_repo = original_repo

        self.assertIsNone(row)
        self.assertIsNone(payload)

    async def test_save_technical_cache_skips_duckdb_when_request_writes_disabled(self):
        from src import cache

        calls = []

        class ForbiddenMarketRepo:
            def upsert_technical_cache(self, *args, **kwargs):
                calls.append("write")
                raise AssertionError("DuckDB write should be skipped")

        original_repo = cache.market_repo
        cache.market_repo = ForbiddenMarketRepo()
        try:
            result = await cache._save_technical_cache(
                "FPT",
                None,
                None,
                180,
                180,
                "2026-05-26",
                {"symbol": "FPT"},
            )
        finally:
            cache.market_repo = original_repo

        self.assertIsNone(result)
        self.assertEqual(calls, [])


class EtlMarkerTests(unittest.TestCase):
    def test_write_and_read_etl_marker(self):
        from src.services.etl_marker import read_last_etl_marker, write_last_etl_marker

        with TemporaryDirectory() as tmp:
            marker = write_last_etl_marker(
                repo_root=Path(tmp),
                run_id="20260527T001500",
                data_date="2026-05-26",
                status="success",
                symbols=["FPT", "ACB"],
            )
            loaded = read_last_etl_marker(repo_root=Path(tmp))
            marker_exists = marker.exists()

        self.assertTrue(marker_exists)
        self.assertEqual(loaded["run_id"], "20260527T001500")
        self.assertEqual(loaded["data_date"], "2026-05-26")
        self.assertEqual(loaded["status"], "success")
        self.assertEqual(loaded["symbols"], ["FPT", "ACB"])


class OrderSideInferenceTests(unittest.TestCase):
    def test_infers_buy_when_price_moves_up(self):
        from src.services.vnstock_fetcher import _infer_match_type

        match_type, source, confidence = _infer_match_type(
            current_price=75.0,
            previous_price=74.5,
            source_match_type="unknown",
        )

        self.assertEqual((match_type, source, confidence), ("buy", "price_tick", "inferred"))

    def test_infers_sell_when_price_moves_down(self):
        from src.services.vnstock_fetcher import _infer_match_type

        match_type, source, confidence = _infer_match_type(
            current_price=74.0,
            previous_price=74.5,
            source_match_type="unknown",
        )

        self.assertEqual((match_type, source, confidence), ("sell", "price_tick", "inferred"))

    def test_keeps_unknown_when_price_is_unchanged(self):
        from src.services.vnstock_fetcher import _infer_match_type

        match_type, source, confidence = _infer_match_type(
            current_price=74.5,
            previous_price=74.5,
            source_match_type="unknown",
        )

        self.assertEqual((match_type, source, confidence), ("unknown", "price_tick", "unknown"))


class ValuationExtractionTests(unittest.TestCase):
    def test_extracts_normalized_ratio_records(self):
        from src.utils import _extract_valuation_from_ratios

        valuation = _extract_valuation_from_ratios(
            [
                {
                    "period": "2026-Q1",
                    "eps": 6016.81,
                    "pe": 15.92,
                    "pb": 3.73,
                    "roe": 5.78,
                    "roa": 2.93,
                }
            ]
        )

        self.assertEqual(
            valuation,
            {
                "pe": 15.92,
                "pb": 3.73,
                "eps": 6016.81,
                "roe": 5.78,
                "roa": 2.93,
                "market_cap": None,
            },
        )


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

    async def test_lifespan_continues_when_ai_requeue_storage_is_unavailable(self):
        from src.jobs import build_lifespan

        calls = []

        def init_db():
            calls.append("init_db")

        class FailingAiJobRepo:
            def load_ai_jobs_by_status(self, status):
                calls.append(f"load:{status}")
                raise OSError("warehouse is locked")

        class AiJobService:
            async def requeue_existing(self, job_ids):
                calls.append(f"requeue:{job_ids}")

            def ensure_worker(self):
                calls.append("ensure_worker")

        class App:
            pass

        lifespan = build_lifespan(
            init_db=init_db,
            ai_job_repo=FailingAiJobRepo(),
            ai_job_service=AiJobService(),
        )
        async with lifespan(App()):
            calls.append("inside")

        self.assertEqual(calls, ["init_db", "load:queued", "inside"])


class StockReadApiSnapshotModeTests(unittest.IsolatedAsyncioTestCase):
    async def test_snapshot_refresh_param_is_rejected(self):
        from src.routes.stocks import get_snapshots

        with self.assertRaises(HTTPException) as ctx:
            await get_snapshots(symbols="FPT", refresh=True)

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail["code"], "REFRESH_DISABLED_IN_SNAPSHOT_MODE")

    async def test_legacy_manual_order_tick_time_is_shifted_back_to_vietnam_session(self):
        from src.routes.stocks import _normalize_legacy_manual_tick_time

        tick = _normalize_legacy_manual_tick_time(
            {
                "id": "manual|FPT|2026-05-29T17:20:21+07:00|24.9|490",
                "symbol": "FPT",
                "time": "2026-05-29T17:20:21+07:00",
                "price": 24.9,
                "volume": 490,
                "match_type": "manual",
            }
        )

        self.assertEqual(tick["time"], "2026-05-29T10:20:21+07:00")

    async def test_ticks_response_preserves_side_metadata(self):
        from src.routes import stocks

        class Fetcher:
            last_intraday_sync_at = None

            def is_intraday_fetch_window(self):
                return True

            def get_intraday_cache_view(self, symbols, limit):
                return {
                    "FPT": [
                        {
                            "id": "1",
                            "symbol": "FPT",
                            "time": "2026-05-29T10:20:21+07:00",
                            "price": 74.5,
                            "volume": 100,
                            "match_type": "buy",
                            "side_source": "price_tick",
                            "side_confidence": "inferred",
                        }
                    ]
                }

        async def fake_refresh(symbols):
            return {"status": "cached"}

        original_fetcher = stocks.fetcher_service
        original_refresh = stocks._refresh_dnse_realtime
        stocks.fetcher_service = Fetcher()
        stocks._refresh_dnse_realtime = fake_refresh
        try:
            response = await stocks.get_ticks("FPT", limit=10)
        finally:
            stocks.fetcher_service = original_fetcher
            stocks._refresh_dnse_realtime = original_refresh

        tick = response["ticks"][0]
        self.assertEqual(tick["match_type"], "buy")
        self.assertEqual(tick["side_source"], "price_tick")
        self.assertEqual(tick["side_confidence"], "inferred")

    async def test_intraday_accepts_four_hour_interval(self):
        import inspect

        from src.routes import stocks

        interval_default = inspect.signature(stocks.get_intraday).parameters["interval_minutes"].default
        max_interval = next(
            item.le for item in interval_default.metadata if hasattr(item, "le")
        )
        self.assertEqual(max_interval, 240)

        class Fetcher:
            last_intraday_sync_at = None

            def is_intraday_fetch_window(self):
                return False

            def get_intraday_cache_view(self, symbols, limit):
                return {"FPT": []}

        async def fake_refresh(symbols):
            return {"status": "cached"}

        original_fetcher = stocks.fetcher_service
        original_refresh = stocks._refresh_dnse_realtime
        original_lake_reader = stocks.read_latest_session_ticks_from_parquet
        stocks.fetcher_service = Fetcher()
        stocks._refresh_dnse_realtime = fake_refresh
        stocks.read_latest_session_ticks_from_parquet = lambda symbol, limit: []
        try:
            response = await stocks.get_intraday("FPT", limit=10, interval_minutes=240)
        finally:
            stocks.fetcher_service = original_fetcher
            stocks._refresh_dnse_realtime = original_refresh
            stocks.read_latest_session_ticks_from_parquet = original_lake_reader

        self.assertEqual(response["symbol"], "FPT")
        self.assertEqual(response["interval_minutes"], 240)
        self.assertEqual(response["data"], [])

    async def test_intraday_falls_back_to_latest_session_parquet_when_cache_empty(self):
        from src.routes import stocks

        class Fetcher:
            last_intraday_sync_at = None

            def is_intraday_fetch_window(self):
                return False

            def get_intraday_cache_view(self, symbols, limit):
                return {"FPT": []}

        async def fake_refresh(symbols):
            return {"status": "cached"}

        def fake_lake_reader(symbol, limit=None):
            self.assertEqual(symbol, "FPT")
            return [
                {
                    "id": "dnse-historical|FPT|2026-06-08T09:01:00+07:00|118.5|100",
                    "symbol": "FPT",
                    "time": "2026-06-08T09:01:00+07:00",
                    "price": 118.5,
                    "volume": 100,
                    "match_type": "buy",
                    "side_source": "dnse",
                    "side_confidence": "source",
                    "source": "dnse_historical",
                },
                {
                    "id": "dnse-historical|FPT|2026-06-08T09:01:30+07:00|119.0|50",
                    "symbol": "FPT",
                    "time": "2026-06-08T09:01:30+07:00",
                    "price": 119.0,
                    "volume": 50,
                    "match_type": "sell",
                    "side_source": "dnse",
                    "side_confidence": "source",
                    "source": "dnse_historical",
                },
            ]

        original_fetcher = stocks.fetcher_service
        original_refresh = stocks._refresh_dnse_realtime
        original_lake_reader = stocks.read_latest_session_ticks_from_parquet
        stocks.fetcher_service = Fetcher()
        stocks._refresh_dnse_realtime = fake_refresh
        stocks.read_latest_session_ticks_from_parquet = fake_lake_reader
        try:
            response = await stocks.get_intraday("FPT", limit=10, interval_minutes=1)
        finally:
            stocks.fetcher_service = original_fetcher
            stocks._refresh_dnse_realtime = original_refresh
            stocks.read_latest_session_ticks_from_parquet = original_lake_reader

        self.assertEqual(response["source"], "intraday-parquet")
        self.assertEqual(response["ticks_count"], 2)
        self.assertEqual(
            response["data"],
            [
                {
                    "time": "2026-06-08T09:01:00+07:00",
                    "open": 118.5,
                    "high": 119.0,
                    "low": 118.5,
                    "close": 119.0,
                    "volume": 150,
                }
            ],
        )

    async def test_intraday_parquet_fallback_limits_after_aggregating_full_session(self):
        from src.routes import stocks

        class Fetcher:
            last_intraday_sync_at = None

            def is_intraday_fetch_window(self):
                return False

            def get_intraday_cache_view(self, symbols, limit):
                return {"STB": []}

        async def fake_refresh(symbols):
            return {"status": "cached"}

        def fake_lake_reader(symbol, limit=None):
            self.assertEqual(symbol, "STB")
            self.assertIsNone(limit)
            return [
                {
                    "symbol": "STB",
                    "time": "2026-06-09T09:15:00+07:00",
                    "price": 70.0,
                    "volume": 100,
                    "source": "dnse_historical",
                },
                *[
                    {
                        "symbol": "STB",
                        "time": f"2026-06-09T13:{minute:02d}:00+07:00",
                        "price": 72.0,
                        "volume": 10,
                        "source": "dnse_historical",
                    }
                    for minute in range(20)
                ],
            ]

        original_fetcher = stocks.fetcher_service
        original_refresh = stocks._refresh_dnse_realtime
        original_lake_reader = stocks.read_latest_session_ticks_from_parquet
        stocks.fetcher_service = Fetcher()
        stocks._refresh_dnse_realtime = fake_refresh
        stocks.read_latest_session_ticks_from_parquet = fake_lake_reader
        try:
            response = await stocks.get_intraday("STB", limit=360, interval_minutes=1)
        finally:
            stocks.fetcher_service = original_fetcher
            stocks._refresh_dnse_realtime = original_refresh
            stocks.read_latest_session_ticks_from_parquet = original_lake_reader

        self.assertEqual(response["source"], "intraday-parquet")
        self.assertEqual(response["data"][0]["time"], "2026-06-09T09:15:00+07:00")
        self.assertEqual(response["count"], 21)

    async def test_ticks_falls_back_to_latest_session_parquet_when_cache_empty(self):
        from src.routes import stocks

        class Fetcher:
            last_intraday_sync_at = None

            def is_intraday_fetch_window(self):
                return False

            def get_intraday_cache_view(self, symbols, limit):
                return {"FPT": []}

        async def fake_refresh(symbols):
            return {"status": "cached"}

        def fake_lake_reader(symbol, limit=None):
            return [
                {
                    "id": "dnse-historical|FPT|2026-06-08T09:01:00+07:00|118.5|100",
                    "symbol": symbol,
                    "time": "2026-06-08T09:01:00+07:00",
                    "price": 118.5,
                    "volume": 100,
                    "match_type": "buy",
                    "side_source": "dnse",
                    "side_confidence": "source",
                    "source": "dnse_historical",
                }
            ]

        original_fetcher = stocks.fetcher_service
        original_refresh = stocks._refresh_dnse_realtime
        original_lake_reader = stocks.read_latest_session_ticks_from_parquet
        stocks.fetcher_service = Fetcher()
        stocks._refresh_dnse_realtime = fake_refresh
        stocks.read_latest_session_ticks_from_parquet = fake_lake_reader
        try:
            response = await stocks.get_ticks("FPT", limit=10)
        finally:
            stocks.fetcher_service = original_fetcher
            stocks._refresh_dnse_realtime = original_refresh
            stocks.read_latest_session_ticks_from_parquet = original_lake_reader

        self.assertEqual(response["source"], "intraday-parquet")
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["ticks"][0]["match_type"], "buy")

    async def test_history_does_not_auto_fetch_when_db_empty(self):
        from src.routes import stocks

        async def empty_history(*args, **kwargs):
            return []

        async def forbidden_refresh(*args, **kwargs):
            raise AssertionError("read API attempted to create market data")

        original_load = stocks.fetcher_service.load_history_from_db_async
        original_refresh = stocks.fetcher_service.refresh_history_for_symbol
        original_root = stocks.REPO_ROOT
        stocks.fetcher_service.load_history_from_db_async = empty_history
        stocks.fetcher_service.refresh_history_for_symbol = forbidden_refresh
        try:
            with TemporaryDirectory() as tmp:
                stocks.REPO_ROOT = Path(tmp)
                result = await stocks.get_history("FPT", limit=30)
        finally:
            stocks.fetcher_service.load_history_from_db_async = original_load
            stocks.fetcher_service.refresh_history_for_symbol = original_refresh
            stocks.REPO_ROOT = original_root

        self.assertEqual(result["data_status"], "NO_DATA_IN_SNAPSHOT")
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["data"], [])

    async def test_history_returns_empty_when_duckdb_is_unavailable(self):
        from src.services import vnstock_fetcher

        class UnavailableMarketRepo:
            def load_history(self, *args, **kwargs):
                raise OSError("duckdb locked")

        original_repo = vnstock_fetcher.market_repo
        vnstock_fetcher.market_repo = UnavailableMarketRepo()
        try:
            rows = await vnstock_fetcher.fetcher_service.load_history_from_db_async("FPT", limit=30)
        finally:
            vnstock_fetcher.market_repo = original_repo

        self.assertEqual(rows, [])

    async def test_history_data_falls_back_to_gold_lake_when_duckdb_is_empty(self):
        from src.routes import stocks

        async def empty_history(*args, **kwargs):
            return []

        original_load = stocks.fetcher_service.load_history_from_db_async
        original_root = stocks.REPO_ROOT

        with TemporaryDirectory() as tmp:
            lake_path = Path(tmp) / "lake" / "gold" / "market_features" / "by_symbol" / "symbol=FPT"
            lake_path.mkdir(parents=True)
            pd.DataFrame(
                [
                    {
                        "symbol": "FPT",
                        "data_date": "2026-05-25",
                        "open_price": 73.5,
                        "high_price": 75.0,
                        "low_price": 73.0,
                        "close_price": 74.0,
                        "volume": 1000,
                    },
                    {
                        "symbol": "FPT",
                        "data_date": "2026-05-26",
                        "open_price": 74.0,
                        "high_price": 75.5,
                        "low_price": 73.5,
                        "close_price": 74.5,
                        "volume": 2000,
                    },
                ]
            ).to_parquet(lake_path / "latest.parquet", index=False)

            stocks.fetcher_service.load_history_from_db_async = empty_history
            stocks.REPO_ROOT = Path(tmp)
            try:
                records = await stocks._load_history_data("FPT", start_date=None, end_date=None, limit=1)
            finally:
                stocks.fetcher_service.load_history_from_db_async = original_load
                stocks.REPO_ROOT = original_root

        self.assertEqual(
            records,
            [
                {
                    "time": "2026-05-26",
                    "open": 74.0,
                    "high": 75.5,
                    "low": 73.5,
                    "close": 74.5,
                    "volume": 2000,
                }
            ],
        )

    async def test_snapshot_uses_eod_history_when_cached_price_is_empty(self):
        from src.services import vnstock_fetcher

        class HistoryMarketRepo:
            def load_history(self, symbol, start_date=None, end_date=None, limit=365):
                return [
                    {"time": "2026-05-24", "open": 38, "high": 39, "low": 37, "close": 38.5, "volume": 1000},
                    {"time": "2026-05-25", "open": 39, "high": 40, "low": 38, "close": 39.5, "volume": 2000},
                ]

        original_repo = vnstock_fetcher.market_repo
        vnstock_fetcher.market_repo = HistoryMarketRepo()
        try:
            snapshot = vnstock_fetcher.fetcher_service.get_snapshot("FPT")
        finally:
            vnstock_fetcher.market_repo = original_repo

        self.assertEqual(snapshot["price"], 39.5)
        self.assertEqual(snapshot["priceSource"], "eod_snapshot")
        self.assertEqual(snapshot["dataStatus"], "DATA_AVAILABLE")

    async def test_snapshot_marks_no_data_when_no_price_source_exists(self):
        from src.services import vnstock_fetcher

        class EmptyMarketRepo:
            def load_history(self, symbol, start_date=None, end_date=None, limit=365):
                return []

        original_repo = vnstock_fetcher.market_repo
        vnstock_fetcher.market_repo = EmptyMarketRepo()
        try:
            snapshot = vnstock_fetcher.fetcher_service.get_snapshot("PLX")
        finally:
            vnstock_fetcher.market_repo = original_repo

        self.assertEqual(snapshot["price"], 0.0)
        self.assertEqual(snapshot["priceSource"], "no_data")
        self.assertEqual(snapshot["dataStatus"], "NO_DATA_IN_SNAPSHOT")

    async def test_overview_falls_back_to_market_cap_from_shares(self):
        from src.routes import stocks

        class Fetcher:
            def get_snapshot(self, symbol):
                return {
                    "price": 74.5,
                    "change": 0,
                    "changePercent": 0,
                    "volume": 1000,
                    "lastUpdate": "2026-05-29T10:00:00+07:00",
                    "syncedAt": "2026-05-29T10:00:00+07:00",
                }

        async def fake_symbol_cache(*args, **kwargs):
            return ({"company_name": "FPT", "outstanding_shares": 1_471_069_000}, "2026-05-29T00:00:00+07:00")

        async def fake_financial_cache(*args, **kwargs):
            return ([{"period": "2026-Q1", "pe": 15.92}], "2026-05-29T00:00:00+07:00")

        original_fetcher = stocks.fetcher_service
        original_symbol_cache = stocks._load_symbol_payload_cache
        original_financial_cache = stocks._load_financial_report_cache
        stocks.fetcher_service = Fetcher()
        stocks._load_symbol_payload_cache = fake_symbol_cache
        stocks._load_financial_report_cache = fake_financial_cache
        try:
            response = await stocks.get_overview("FPT")
        finally:
            stocks.fetcher_service = original_fetcher
            stocks._load_symbol_payload_cache = original_symbol_cache
            stocks._load_financial_report_cache = original_financial_cache

        self.assertEqual(response["pe"], 15.92)
        self.assertEqual(response["market_cap"], 74.5 * 1000 * 1_471_069_000)


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


class MarketIndexScaleTests(unittest.TestCase):
    def test_market_index_quote_expands_thousand_unit_values(self):
        from src.routes.market import _build_market_index_quote

        quote = _build_market_index_quote(
            "VNINDEX",
            [
                {"time": "2026-05-25", "close": 1.89, "volume": 100},
                {"time": "2026-05-26", "close": 1.88, "volume": 200},
            ],
        )

        self.assertEqual(quote["price"], 1880.0)
        self.assertEqual(quote["change"], -10.0)
        self.assertEqual(quote["changePercent"], -0.53)


if __name__ == "__main__":
    unittest.main()
