"""Caching initialization module."""

from collections.abc import Callable
from typing import TypeVar, cast

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend

from app.api.constants import CACHE_DEFAULT_TTL_SECONDS, CACHE_PREFIX
from app.core.config import settings
from app.db.redis_client import redis_client

F = TypeVar("F", bound=Callable[..., object])


def init_redis_caching() -> None:
    """Initialize caching backend."""
    FastAPICache.init(
        RedisBackend(redis_client.client),
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


def cache(*, expire: int | None = None) -> Callable[[F], F]:
    """Conditionally cache a route handler.

    When `CACHE_ENABLED=false`, this decorator is a no-op (no caching at all).
    When enabled, it delegates to `fastapi_cache.decorator.cache`.
    """
    if not settings.cache_enabled:

        def _noop(func: F) -> F:
            return func

        return _noop

    from fastapi_cache.decorator import cache

    return cast(Callable[[F], F], cache(expire=expire))
