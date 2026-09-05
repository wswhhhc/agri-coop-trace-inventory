"""认证接口的 Redis 失败计数和限流。"""

from __future__ import annotations

import hashlib
from typing import Any, cast

from redis.asyncio import Redis


class RateLimitExceeded(ValueError):
    """登录失败次数超过限制。"""

    def __init__(self, retry_after: int) -> None:
        self.retry_after = max(retry_after, 1)
        super().__init__("登录尝试过于频繁")


_RECORD_FAILURE_SCRIPT = """
local account_count = redis.call('INCR', KEYS[1])
local ip_count = redis.call('INCR', KEYS[2])
if account_count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if ip_count == 1 then
    redis.call('EXPIRE', KEYS[2], ARGV[1])
end
local account_ttl = redis.call('TTL', KEYS[1])
local ip_ttl = redis.call('TTL', KEYS[2])
local retry_after = account_ttl
if ip_ttl > retry_after then
    retry_after = ip_ttl
end
return {account_count, ip_count, retry_after}
"""


class LoginRateLimiter:
    """按账号或来源 IP 限制登录失败次数。"""

    def __init__(
        self,
        redis: Redis,
        *,
        key_prefix: str,
        max_attempts: int,
        window_seconds: int = 60,
    ) -> None:
        if max_attempts <= 0 or window_seconds <= 0:
            raise ValueError("限流阈值和窗口必须大于 0")
        self.redis = redis
        self.key_prefix = key_prefix
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    async def ensure_allowed(self, username: str, client_ip: str) -> None:
        """在执行用户查询和密码校验前检查账号及 IP 是否已被限制。"""
        values = await cast(Any, self.redis.mget)(
            self._account_key(username), self._ip_key(client_ip)
        )
        counts = [int(value) for value in values if value is not None]
        if counts and max(counts) >= self.max_attempts:
            ttl = await self._max_ttl(username, client_ip)
            raise RateLimitExceeded(ttl)

    async def record_failure(self, username: str, client_ip: str) -> None:
        """原子记录一次失败；超过阈值后阻止后续登录请求。"""
        result = await cast(Any, self.redis.eval)(
            _RECORD_FAILURE_SCRIPT,
            2,
            self._account_key(username),
            self._ip_key(client_ip),
            str(self.window_seconds),
        )
        if max(int(result[0]), int(result[1])) > self.max_attempts:
            raise RateLimitExceeded(int(result[2]))

    async def reset_account(self, username: str) -> None:
        """登录成功后清除该账号的失败计数。"""
        await cast(Any, self.redis.delete)(self._account_key(username))

    async def _max_ttl(self, username: str, client_ip: str) -> int:
        ttls = await cast(Any, self.redis.ttl)(self._account_key(username))
        ip_ttl = await cast(Any, self.redis.ttl)(self._ip_key(client_ip))
        return max(int(ttls), int(ip_ttl), 1)

    def _account_key(self, username: str) -> str:
        return self._key("account", username)

    def _ip_key(self, client_ip: str) -> str:
        return self._key("ip", client_ip)

    def _key(self, kind: str, value: str) -> str:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return f"{self.key_prefix}auth:fail:{kind}:{digest}"


__all__ = ["LoginRateLimiter", "RateLimitExceeded"]
