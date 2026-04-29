import asyncio
import functools
import logging
import time
from typing import Any, Callable, Optional

_last_timings: dict[str, float] = {}

logger = logging.getLogger(__name__)


def get_last_timing(label: str) -> Optional[float]:
    return _last_timings.get(label)


def timed_log(label: str, threshold_ms: Optional[float] = None) -> Callable:
    """Decorator that logs execution time and stores it for /health.

    threshold_ms: WARNING if exceeded. None → reads settings.perf_warn_threshold_ms.
    """
    def decorator(fn: Callable) -> Callable:
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                t0 = time.perf_counter()
                try:
                    return await fn(*args, **kwargs)
                finally:
                    _record(label, (time.perf_counter() - t0) * 1000, threshold_ms)
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                t0 = time.perf_counter()
                try:
                    return fn(*args, **kwargs)
                finally:
                    _record(label, (time.perf_counter() - t0) * 1000, threshold_ms)
            return sync_wrapper
    return decorator


def _record(label: str, elapsed_ms: float, threshold_ms: Optional[float]) -> None:
    _last_timings[label] = round(elapsed_ms)
    if threshold_ms is None:
        from src.config import settings as _s
        threshold_ms = _s.perf_warn_threshold_ms
    if elapsed_ms >= threshold_ms:
        logger.warning("%s finished in %.0f ms (threshold %.0f ms)", label, elapsed_ms, threshold_ms)
    else:
        logger.info("%s finished in %.0f ms", label, elapsed_ms)
