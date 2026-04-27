from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


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

        if not scheduler.get_job("vn30-eod-job"):
            scheduler.add_job(
                lambda: fetcher_service.aggregate_today_intraday_to_daily(),
                "cron",
                id="vn30-eod-job",
                day_of_week="mon-fri",
                hour=15,
                minute=15,
            )
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