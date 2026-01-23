"""Redis client setup using aioredis."""

from redis.asyncio import ConnectionPool, Redis, RedisError

from app.core.config import settings
from app.core.logger import logger


class RedisClient:
    """Asynchronous Redis client wrapper."""

    def __init__(self) -> None:
        """Initialize the Redis client."""
        self._client: Redis | None = None  # type: ignore [no-any-unimported]
        self._pool: ConnectionPool | None = None  # type: ignore [no-any-unimported]

    async def connect(self) -> None:
        """Establish connection to the Redis server."""
        if self._client is not None:
            return

        self._pool = ConnectionPool.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
        )
        self._client = Redis(connection_pool=self._pool)

        try:
            await self._client.ping()
            logger.info("redis_connected_successfully")
        except RedisError as e:
            logger.error(f"redis_connection_failed: {e}")
            raise

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client is not None:
            await self._client.close()
            if self._pool:
                await self._pool.disconnect()
            self._client = None
            self._pool = None
            logger.info("redis_connection_closed")

    @property
    def client(self) -> Redis:  # type: ignore [no-any-unimported]
        """Get the Redis client instance."""
        if self._client is None:
            raise RuntimeError(
                "Redis client not initialized. Call connect() first or use lifespan."
            )
        return self._client


redis_client = RedisClient()
