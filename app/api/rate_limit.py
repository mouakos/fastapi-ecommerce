"""Initialize rate limiting for the FastAPI application."""

from collections.abc import Callable
from typing import Any

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from app.core.config import settings
from app.db.redis_client import redis_client


async def init_redis_rate_limiter() -> None:
    """Initialize the rate limiter with the Redis client."""
    await FastAPILimiter.init(redis_client.client)


def rate_limit(
    *, times: int, milliseconds: int, seconds: int, minutes: int, hours: int
) -> Callable[..., Any]:
    """Create a rate limiter dependency.

    Args:
        times (int): Number of allowed requests.
        milliseconds (int): Time window in milliseconds.
        seconds (int): Time window in seconds.
        minutes (int): Time window in minutes.
        hours (int): Time window in hours.

    Returns:
        Callable[..., Any]: A dependency callable to be used via Depends(...).
    """
    if not settings.rate_limiting_enabled:

        async def _noop_limiter() -> None:
            return None

        return _noop_limiter

    return RateLimiter(
        times=times, milliseconds=milliseconds, seconds=seconds, minutes=minutes, hours=hours
    )
