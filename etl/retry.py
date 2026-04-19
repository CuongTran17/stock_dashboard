"""Decorator retry dùng chung cho các lời gọi API (vnstock / requests).

Dùng ``tenacity`` với exponential backoff + jitter nhẹ. Chỉ retry trên các
exception "transient" (timeout, connection reset, HTTPError 5xx/429).

Ví dụ::

    from etl.retry import with_retry

    @with_retry()
    def fetch_prices(symbol: str) -> pd.DataFrame:
        ...
"""
from __future__ import annotations

import logging
from typing import Callable, TypeVar

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

log = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)

# Exception base cho phép retry.
_TRANSIENT_EXC: tuple[type[BaseException], ...] = (
    requests.ConnectionError,
    requests.Timeout,
    ConnectionError,
    TimeoutError,
)

# HTTP status codes đáng retry khi thư viện raise ``HTTPError``.
_RETRY_STATUS_CODES: set[int] = {408, 425, 429, 500, 502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, _TRANSIENT_EXC):
        return True
    if isinstance(exc, requests.HTTPError):
        resp = getattr(exc, "response", None)
        if resp is not None and resp.status_code in _RETRY_STATUS_CODES:
            return True
    # vnstock đôi khi raise Exception chung chung với thông báo có "timeout"
    message = str(exc).lower()
    return any(token in message for token in ("timeout", "timed out", "temporarily", "rate limit"))


def with_retry(
    attempts: int = 5,
    min_wait: float = 2.0,
    max_wait: float = 30.0,
) -> Callable[[F], F]:
    """Decorator factory: wrap hàm I/O bằng policy retry có backoff."""
    def decorator(func: F) -> F:
        wrapped = retry(
            reraise=True,
            stop=stop_after_attempt(attempts),
            wait=wait_exponential_jitter(initial=min_wait, max=max_wait, jitter=1.5),
            retry=retry_if_exception(_is_retryable),
            before_sleep=before_sleep_log(log, logging.WARNING),
        )(func)
        return wrapped  # type: ignore[return-value]
    return decorator
