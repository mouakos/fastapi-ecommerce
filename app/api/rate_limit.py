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
    *, times: int = 1, milliseconds: int = 0, seconds: int = 0, minutes: int = 0, hours: int = 0
) -> Callable[..., Any]:
    """Create a rate limiter dependency.

    Args:
        times (int, optional): Number of allowed requests. Defaults to 1.
        milliseconds (int, optional): Time window in milliseconds. Defaults to 0.
        seconds (int, optional): Time window in seconds. Defaults to 0.
        minutes (int, optional): Time window in minutes. Defaults to 0.
        hours (int, optional): Time window in hours. Defaults to 0.

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
