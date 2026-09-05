"""Redis 客户端生命周期管理。"""

from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import Settings

redis_client: Redis | None = None


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


def get_redis_client() -> Redis:
    """获取已初始化的 Redis 客户端。"""
    if redis_client is None:
        raise RuntimeError("Redis 尚未初始化")
    return redis_client


async def dispose_redis_client() -> None:
    """释放进程级 Redis 连接池。"""
    global redis_client

    if redis_client is not None:
        await redis_client.aclose()
    redis_client = None


__all__ = [
    "create_redis_client",
    "dispose_redis_client",
    "get_redis_client",
    "initialize_redis",
    "redis_client",
]
