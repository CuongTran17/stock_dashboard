from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Callable

logger = logging.getLogger(__name__)


def build_lifespan(*, init_db: Callable[[], None]) -> Callable[[Any], Any]:
    @asynccontextmanager
    async def lifespan(app: Any):
        del app
        logger.info("Initializing application schema in strict snapshot mode...")
        init_db()
        logger.info("Market data startup is read-only; no fetch loops, preload jobs, or ETL schedulers were started.")
        yield

    return lifespan
