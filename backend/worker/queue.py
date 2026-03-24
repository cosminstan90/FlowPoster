"""
ARQ Redis pool connection factory.

Usage in routes::

    redis = await get_arq_pool()
    try:
        await redis.enqueue_job("task_name", arg1, arg2)
    finally:
        await redis.aclose()

Usage in worker startup::

    async def startup(ctx: dict) -> None:
        ctx["arq"] = await get_arq_pool()
"""

from __future__ import annotations

from arq.connections import ArqRedis, RedisSettings, create_pool

from backend.config import settings

_redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)


async def get_arq_pool() -> ArqRedis:
    """Create and return a new ARQ Redis connection pool."""
    return await create_pool(_redis_settings)
