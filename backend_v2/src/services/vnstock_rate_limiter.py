import asyncio
import os
import time


class VnstockRateLimiter:
    def __init__(self) -> None:
        configured_interval = float(os.getenv("VNSTOCK_MIN_REQUEST_INTERVAL_SECONDS", "1.05"))
        max_per_minute = max(int(os.getenv("VNSTOCK_MAX_REQUESTS_PER_MINUTE", "55")), 1)
        min_interval_from_quota = 60.0 / float(max_per_minute)

        # Keep a conservative pacing for community quota and allow override via env.
        self.min_interval_seconds = max(configured_interval, min_interval_from_quota, 0.6)
        self._lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < self.min_interval_seconds:
                await asyncio.sleep(self.min_interval_seconds - elapsed)
            self._last_request_at = time.monotonic()


vnstock_rate_limiter = VnstockRateLimiter()
