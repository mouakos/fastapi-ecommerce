"""Caching initialization module."""

from collections.abc import Callable
from typing import TypeVar, cast

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis.asyncio import Redis

from app.core.config import settings

F = TypeVar("F", bound=Callable[..., object])

CACHE_PREFIX = "e-commerce"
CACHE_DEFAULT_TTL_SECONDS = 60


def init_redis_caching(client: Redis) -> None:  # type: ignore [no-any-unimported]
    """Initialize caching backend.

    Args:
        client (Redis): Redis client instance.
    """
    FastAPICache.init(
        RedisBackend(client),
        prefix=CACHE_PREFIX,
        expire=CACHE_DEFAULT_TTL_SECONDS,
    )


def init_in_memory_caching() -> None:
    """Initialize in-memory caching backend."""
    FastAPICache.init(
        InMemoryBackend(),
        prefix=CACHE_PREFIX,
        expire=CACHE_DEFAULT_TTL_SECONDS,
    )


def cache_if_enabled(*, expire: int | None = None) -> Callable[[F], F]:
    """Conditionally cache a route handler.

    When `CACHE_ENABLED=false`, this decorator is a no-op (no caching at all).
    When enabled, it delegates to `fastapi_cache.decorator.cache`.
    """
    if not settings.cache_enabled:

        def _noop(func: F) -> F:
            return func

        return _noop

    return cast(Callable[[F], F], cache(expire=expire))
