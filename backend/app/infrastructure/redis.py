"""Redis 客户端生命周期管理。"""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings

redis_client: Redis | None = None
_redis_loop: asyncio.AbstractEventLoop | None = None


def create_redis_client(settings: Settings) -> Redis:
    """创建异步 Redis 客户端；创建时不主动建立网络连接。"""
    return Redis.from_url(
        settings.redis_url.get_secret_value(),
        decode_responses=True,
        socket_timeout=settings.redis_socket_timeout_seconds,
        socket_connect_timeout=settings.redis_socket_timeout_seconds,
        max_connections=settings.redis_max_connections,
        health_check_interval=30,
    )


def initialize_redis(settings: Settings) -> Redis:
    """初始化进程级 Redis 客户端。"""
    global redis_client

    if redis_client is None:
        redis_client = create_redis_client(settings)
    return redis_client


def get_redis_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Redis:
    """获取已初始化的 Redis 客户端。"""
    global _redis_loop, redis_client

    current_loop: asyncio.AbstractEventLoop | None
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if redis_client is None:
        redis_client = create_redis_client(settings)
    if current_loop is not None and _redis_loop is None:
        _redis_loop = current_loop
    elif current_loop is not None and _redis_loop is not current_loop:
        previous_client = redis_client
        redis_client = create_redis_client(settings)
        _redis_loop = current_loop
        if previous_client is not redis_client:
            asyncio.create_task(previous_client.aclose())
    return redis_client


async def dispose_redis_client() -> None:
    """释放进程级 Redis 连接池。"""
    global _redis_loop, redis_client

    if redis_client is not None:
        try:
            await redis_client.aclose()
        except (RedisError, OSError, RuntimeError):
            # 关闭阶段可能遇到已结束的事件循环或已断开的连接，
            # 不能让资源清理异常覆盖应用的原始退出路径。
            pass
        finally:
            redis_client = None
            _redis_loop = None


__all__ = [
    "create_redis_client",
    "dispose_redis_client",
    "get_redis_client",
    "initialize_redis",
    "redis_client",
]
