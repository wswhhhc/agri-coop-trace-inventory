"""公开追溯和二维码接口的 Redis IP 限流。"""

from __future__ import annotations

import hashlib
from typing import Any, cast

from redis.asyncio import Redis
from redis.exceptions import RedisError


class PublicRateLimitExceeded(ValueError):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = max(retry_after, 1)
        super().__init__("公开接口请求过于频繁")


_INCREMENT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {count, ttl}
"""


class PublicRateLimiter:
    """为不同公开资源使用独立 Redis 计数键。"""

    def __init__(
        self,
        redis: Redis,
        *,
        key_prefix: str,
        resource: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> None:
        if max_requests <= 0 or window_seconds <= 0:
            raise ValueError("限流阈值和窗口必须大于 0")
        self.redis = redis
        self.key_prefix = key_prefix
        self.resource = resource
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def ensure_allowed(self, client_ip: str) -> None:
        try:
            result = await cast(Any, self.redis.eval)(
                _INCREMENT_SCRIPT,
                1,
                self._key(client_ip),
                str(self.window_seconds),
            )
        except (RedisError, OSError, RuntimeError) as exc:
            raise PublicRateLimiterDependencyError from exc
        count, retry_after = int(result[0]), max(int(result[1]), 1)
        if count > self.max_requests:
            raise PublicRateLimitExceeded(retry_after)

    def _key(self, client_ip: str) -> str:
        digest = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
        return f"{self.key_prefix}public:{self.resource}:ip:{digest}"


class PublicRateLimiterDependencyError(RuntimeError):
    """Redis 不可用，无法安全执行公开接口限流。"""


__all__ = [
    "PublicRateLimitExceeded",
    "PublicRateLimiter",
    "PublicRateLimiterDependencyError",
]
