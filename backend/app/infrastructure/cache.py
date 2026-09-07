"""可重建 JSON 查询缓存和范围安全的缓存键工具。"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import secrets
from collections.abc import Awaitable, Callable, Mapping
from datetime import date, datetime
from typing import Any, TypeVar, cast
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)
T = TypeVar("T")

_RELEASE_REBUILD_LOCK_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


def _normalize(value: Any) -> Any:
    """将范围和查询参数转换为稳定、可 JSON 编码的结构。"""
    if isinstance(value, Mapping):
        return {
            str(key): _normalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (set, frozenset)):
        normalized = [_normalize(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, default=str))
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, (UUID, date, datetime)):
        return str(value)
    return value


class CacheKeyBuilder:
    """构造包含数据范围和筛选条件的哈希缓存键。"""

    def __init__(self, key_prefix: str) -> None:
        self.key_prefix = key_prefix

    def build(
        self,
        resource: str,
        *,
        scope: Mapping[str, Any],
        filters: Mapping[str, Any] | None = None,
    ) -> str:
        if not resource or ":" in resource:
            raise ValueError("缓存资源名不能为空且不能包含冒号")
        document = {
            "scope": _normalize(scope),
            "filters": _normalize(filters or {}),
        }
        digest = hashlib.sha256(
            json.dumps(document, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()
        return f"{self.key_prefix}query:{resource}:{digest}"


class JsonCache:
    """支持 TTL 抖动、异常降级和单键重建互斥的 JSON 缓存。"""

    def __init__(
        self,
        redis: Redis,
        *,
        key_prefix: str,
        ttl_seconds: int,
        name: str = "query",
        jitter_ratio: float = 0.1,
        lock_ttl_seconds: int = 5,
        lock_wait_seconds: float = 0.05,
        lock_wait_attempts: int = 3,
        random_fn: Callable[[float, float], float] = random.uniform,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("缓存 TTL 必须大于 0")
        if not 0 <= jitter_ratio <= 1:
            raise ValueError("缓存 TTL 抖动比例必须在 0 到 1 之间")
        if lock_ttl_seconds <= 0 or lock_wait_seconds <= 0 or lock_wait_attempts <= 0:
            raise ValueError("缓存重建锁参数必须大于 0")
        self.redis = redis
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds
        self.name = name
        self.jitter_ratio = jitter_ratio
        self.lock_ttl_seconds = lock_ttl_seconds
        self.lock_wait_seconds = lock_wait_seconds
        self.lock_wait_attempts = lock_wait_attempts
        self.random_fn = random_fn

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self.redis.get(key)
        except (RedisError, OSError, RuntimeError):
            self._log_event("get_error")
            return None
        if raw is None:
            self._log_event("miss")
            return None
        try:
            value = json.loads(raw)
        except (TypeError, ValueError):
            self._log_event("malformed")
            await self.delete(key)
            return None
        self._log_event("hit")
        return value

    async def set(self, key: str, payload: Any, *, ttl_seconds: int | None = None) -> None:
        base_ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        if base_ttl <= 0:
            raise ValueError("缓存 TTL 必须大于 0")
        try:
            await self.redis.set(
                key,
                json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str),
                ex=self.effective_ttl(base_ttl),
            )
            self._log_event("set")
        except (RedisError, OSError, RuntimeError):
            self._log_event("set_error")

    async def delete(self, key: str) -> None:
        try:
            await self.redis.delete(key)
            self._log_event("delete")
        except (RedisError, OSError, RuntimeError):
            self._log_event("delete_error")

    async def ttl(self, key: str) -> int | None:
        try:
            value = await self.redis.ttl(key)
        except (RedisError, OSError, RuntimeError):
            self._log_event("ttl_error")
            return None
        return int(value) if value is not None else None

    async def acquire_rebuild_lock(self, key: str) -> str | None:
        token = secrets.token_urlsafe(16)
        try:
            acquired = await self.redis.set(
                self._lock_key(key),
                token,
                ex=self.lock_ttl_seconds,
                nx=True,
            )
        except (RedisError, OSError, RuntimeError):
            self._log_event("lock_error")
            return None
        if not acquired:
            self._log_event("lock_busy")
            return None
        self._log_event("lock_acquired")
        return token

    async def release_rebuild_lock(self, key: str, token: str) -> bool:
        try:
            result = await cast(Any, self.redis.eval)(
                _RELEASE_REBUILD_LOCK_SCRIPT,
                1,
                self._lock_key(key),
                token,
            )
        except (RedisError, OSError, RuntimeError):
            self._log_event("unlock_error")
            return False
        return bool(result)

    async def get_or_set(
        self,
        key: str,
        loader: Callable[[], Awaitable[T]],
        *,
        ttl_seconds: int | None = None,
    ) -> T | Any:
        """缓存未命中时单键重建，避免并发请求重复访问数据库。"""
        cached = await self.get(key)
        if cached is not None:
            return cached

        token = await self.acquire_rebuild_lock(key)
        if token is None:
            for _ in range(self.lock_wait_attempts):
                await asyncio.sleep(self.lock_wait_seconds)
                cached = await self.get(key)
                if cached is not None:
                    return cached

        if token is None:
            # Redis 故障或持锁方超时不能阻塞业务，允许本次请求回源并尝试写缓存。
            value = await loader()
            await self.set(key, value, ttl_seconds=ttl_seconds)
            return value

        try:
            cached = await self.get(key)
            if cached is not None:
                return cached
            value = await loader()
            await self.set(key, value, ttl_seconds=ttl_seconds)
            return value
        finally:
            await self.release_rebuild_lock(key, token)

    def effective_ttl(self, base_ttl: int | None = None) -> int:
        """返回带随机抖动的 TTL，至少保留 1 秒。"""
        ttl = base_ttl if base_ttl is not None else self.ttl_seconds
        if ttl <= 0:
            raise ValueError("缓存 TTL 必须大于 0")
        if self.jitter_ratio == 0:
            return ttl
        jitter = self.random_fn(-self.jitter_ratio, self.jitter_ratio)
        return max(1, round(ttl * (1 + jitter)))

    def _lock_key(self, key: str) -> str:
        digest = hashlib.sha256(key.encode()).hexdigest()
        return f"{self.key_prefix}lock:query:{digest}"

    def _log_event(self, event: str) -> None:
        logger.debug("cache_event event=%s cache=%s", event, self.name)


__all__ = ["CacheKeyBuilder", "JsonCache"]
