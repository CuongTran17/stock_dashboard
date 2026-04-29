from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def build_lifespan(
    *,
    init_db: Callable[[], None],
    fetcher_service: Any,
    fundamental_service: Any,
    vn30_symbols: list[str],
    preload_reference_cache_enabled: bool,
    preload_reference_force_refresh: bool,
    preload_reference_symbol_limit: int,
) -> Callable[[Any], Any]:
    scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")
    from src.settings import get_settings

    settings = get_settings()

    def _etl_symbols() -> list[str]:
        if settings.etl_symbol_list:
            return settings.etl_symbol_list
        return list(vn30_symbols)

    def _etl_cfg_factory():
        from datetime import date, timedelta

        from etl.config import EtlConfig

        today = date.today()
        return EtlConfig.from_args(
            start_date=today - timedelta(days=settings.etl_lookback_days),
            end_date=today,
            symbols=_etl_symbols(),
            enable_mysql_load=True,
            tick_source=settings.etl_tick_source,
            run_mode=settings.etl_run_mode,
            incremental_overlap_days=settings.etl_incremental_overlap_days,
        )

    async def _warmup_caches() -> None:
        scope = settings.etl_cache_warmup_scope.lower()
        symbols = vn30_symbols if scope == "vn30" else _etl_symbols()
        logger.info("Starting ETL cache warmup scope=%s symbols=%d", scope, len(symbols))
        await fundamental_service.preload_reference_caches(symbols, force_refresh=True)
        await fetcher_service.preload_historical_data(symbols)
        logger.info("ETL cache warmup completed")

    @asynccontextmanager
    async def lifespan(app: Any):
        logger.info("Initializing MySQL schema...")
        init_db()

        from src.services.mock_intraday_streamer import run_mock_streamer

        intraday_task = asyncio.create_task(fetcher_service.fetch_loop(), name="vn30-intraday-fetch")
        history_task = asyncio.create_task(fetcher_service.preload_historical_data(vn30_symbols), name="vn30-history-preload")
        mock_stream_task = asyncio.create_task(run_mock_streamer(fetcher_service), name="vn30-mock-intraday-stream")
        reference_preload_task: Optional[asyncio.Task[Any]] = None

        if preload_reference_cache_enabled:
            preload_symbols = vn30_symbols[:preload_reference_symbol_limit]
            reference_preload_task = asyncio.create_task(
                fundamental_service.preload_reference_caches(
                    preload_symbols,
                    force_refresh=preload_reference_force_refresh,
                ),
                name="vn30-reference-preload",
            )

        legacy_eod_enabled = settings.vn30_eod_job_enabled
        if legacy_eod_enabled and not scheduler.get_job("vn30-eod-job"):
            scheduler.add_job(
                lambda: fetcher_service.aggregate_today_intraday_to_daily(),
                "cron",
                id="vn30-eod-job",
                day_of_week="mon-fri",
                hour=15,
                minute=15,
            )
        elif not legacy_eod_enabled:
            logger.info("Legacy vn30-eod-job disabled; ETL tick EOD aggregation is authoritative")
        try:
            from etl.scheduler import EtlScheduler

            etl_scheduler = EtlScheduler(scheduler=scheduler)
            etl_scheduler.register_jobs(cfg_factory=_etl_cfg_factory, cache_refresh=_warmup_caches)
        except Exception as exc:
            logger.warning("Could not register ETL scheduler jobs: %s", exc)
        if not scheduler.running:
            scheduler.start()

        try:
            yield
        finally:
            fetcher_service.stop()

            running_tasks: list[asyncio.Task[Any]] = [intraday_task, history_task, mock_stream_task]
            if reference_preload_task is not None:
                running_tasks.append(reference_preload_task)

            for task in running_tasks:
                task.cancel()
            await asyncio.gather(*running_tasks, return_exceptions=True)

            try:
                fetcher_service.aggregate_today_intraday_to_daily()
            except Exception as exc:
                logger.warning("EOD aggregation failed during shutdown: %s", exc)

            if scheduler.running:
                scheduler.shutdown(wait=False)

    return lifespan
