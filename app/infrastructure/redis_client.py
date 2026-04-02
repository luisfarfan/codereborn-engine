"""
Async Redis client for CodeReborn Engine.

Used for:
  - Job status pub/sub (notify clients of progress)
  - Rate-limit counters for LLM calls
  - Short-lived caching of stack detection results
"""

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.settings import get_settings

settings = get_settings()

# Module-level client — shared across the application lifetime.
# The pool is managed by the redis library.
_redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    """Return the shared Redis client, initializing it on first call."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis_client() -> None:
    """Close the Redis connection pool (called on app shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    """FastAPI dependency that yields the shared Redis client."""
    client = await get_redis_client()
    yield client
