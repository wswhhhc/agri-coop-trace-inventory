from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.infrastructure.redis import get_redis_client
from app.services.query_cache import QueryCache


def get_reference_query_cache(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> QueryCache:
    return QueryCache(
        redis,
        key_prefix=settings.redis_key_prefix,
        ttl_seconds=settings.reference_cache_ttl_seconds,
        jitter_ratio=settings.cache_ttl_jitter_ratio,
        name="reference",
    )


def get_permission_query_cache(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> QueryCache:
    return QueryCache(
        redis,
        key_prefix=settings.redis_key_prefix,
        ttl_seconds=settings.permission_cache_ttl_seconds,
        jitter_ratio=settings.cache_ttl_jitter_ratio,
        name="permission",
    )


def get_forecasting_query_cache(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> QueryCache:
    return QueryCache(
        redis,
        key_prefix=settings.redis_key_prefix,
        ttl_seconds=settings.forecasting_cache_ttl_seconds,
        jitter_ratio=settings.cache_ttl_jitter_ratio,
        name="forecasting",
    )


def get_detail_query_cache(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> QueryCache:
    return QueryCache(
        redis,
        key_prefix=settings.redis_key_prefix,
        ttl_seconds=settings.detail_cache_ttl_seconds,
        jitter_ratio=settings.cache_ttl_jitter_ratio,
        name="detail",
    )


__all__ = [
    "get_detail_query_cache",
    "get_forecasting_query_cache",
    "get_permission_query_cache",
    "get_reference_query_cache",
]
