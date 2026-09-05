"""基于 Redis 的认证会话和刷新令牌存储。"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from redis.asyncio import Redis


class InvalidRefreshToken(ValueError):
    """刷新令牌不存在、已轮换或对应会话已撤销。"""


@dataclass(frozen=True, slots=True)
class AuthSession:
    """Redis 中认证会话的公开数据。"""

    session_id: str
    user_id: UUID
    session_family: str
    status: str
    refresh_token_hash: str
    created_at: datetime
    last_rotated_at: datetime


@dataclass(frozen=True, slots=True)
class CreatedSession:
    """新建或轮换会话返回的会话数据和明文刷新令牌。"""

    session: AuthSession
    refresh_token: str


_ROTATE_REFRESH_TOKEN_SCRIPT = """
local status = redis.call('HGET', KEYS[1], 'status')
local current_hash = redis.call('HGET', KEYS[1], 'refresh_token_hash')
if status ~= 'ACTIVE' or current_hash ~= ARGV[1] then
    return {0}
end
redis.call('HSET', KEYS[1],
    'refresh_token_hash', ARGV[2],
    'last_rotated_at', ARGV[3]
)
redis.call('EXPIRE', KEYS[1], ARGV[4])
return {
    1,
    redis.call('HGET', KEYS[1], 'user_id'),
    redis.call('HGET', KEYS[1], 'session_family'),
    redis.call('HGET', KEYS[1], 'created_at')
}
"""

_REVOKE_REFRESH_TOKEN_SCRIPT = """
local status = redis.call('HGET', KEYS[1], 'status')
local current_hash = redis.call('HGET', KEYS[1], 'refresh_token_hash')
if status ~= 'ACTIVE' or current_hash ~= ARGV[1] then
    return {0}
end
local user_id = redis.call('HGET', KEYS[1], 'user_id')
redis.call('DEL', KEYS[1])
return {1, user_id}
"""


class RedisSessionStore:
    """封装认证会话的创建、查询、轮换和撤销。"""

    def __init__(
        self,
        redis: Redis,
        *,
        key_prefix: str,
        ttl_seconds: int,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds 必须大于 0")
        self.redis = redis
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds

    async def create(
        self,
        user_id: UUID,
        *,
        now: datetime | None = None,
    ) -> CreatedSession:
        """创建新的认证会话并返回一次性的明文刷新令牌。"""
        session_id = str(uuid4())
        session_family = str(uuid4())
        refresh_token = self._new_refresh_token(session_id)
        current_time = _as_utc(now)
        token_hash = _hash_refresh_token(refresh_token)
        session = AuthSession(
            session_id=session_id,
            user_id=user_id,
            session_family=session_family,
            status="ACTIVE",
            refresh_token_hash=token_hash,
            created_at=current_time,
            last_rotated_at=current_time,
        )

        await cast(Any, self.redis.hset)(
            self._session_key(session_id),
            mapping=self._to_mapping(session),
        )
        await cast(Any, self.redis.expire)(
            self._session_key(session_id), self.ttl_seconds
        )
        return CreatedSession(session=session, refresh_token=refresh_token)

    async def get(self, session_id: str) -> AuthSession | None:
        """按会话 ID 读取会话；不存在时返回 None。"""
        mapping = await cast(Any, self.redis.hgetall)(self._session_key(session_id))
        if not mapping:
            return None
        return self._from_mapping(session_id, mapping)

    async def ttl(self, session_id: str) -> int:
        """返回会话剩余 TTL，供监控和测试使用。"""
        return await cast(Any, self.redis.ttl)(self._session_key(session_id))

    async def rotate(
        self,
        refresh_token: str,
        *,
        now: datetime | None = None,
    ) -> CreatedSession:
        """原子轮换刷新令牌，旧令牌从本次操作后立即失效。"""
        session_id = self.session_id_from_refresh_token(refresh_token)
        new_refresh_token = self._new_refresh_token(session_id)
        current_time = _as_utc(now)
        result = await cast(Any, self.redis.eval)(
            _ROTATE_REFRESH_TOKEN_SCRIPT,
            1,
            self._session_key(session_id),
            _hash_refresh_token(refresh_token),
            _hash_refresh_token(new_refresh_token),
            current_time.isoformat(),
            str(self.ttl_seconds),
        )

        if not result or int(result[0]) != 1:
            raise InvalidRefreshToken("刷新令牌无效")

        session = AuthSession(
            session_id=session_id,
            user_id=UUID(str(result[1])),
            session_family=str(result[2]),
            status="ACTIVE",
            refresh_token_hash=_hash_refresh_token(new_refresh_token),
            created_at=datetime.fromisoformat(str(result[3])),
            last_rotated_at=current_time,
        )
        return CreatedSession(session=session, refresh_token=new_refresh_token)

    async def revoke(self, session_id: str) -> None:
        """立即删除会话，使其关联的刷新令牌全部失效。"""
        await cast(Any, self.redis.delete)(self._session_key(session_id))

    async def revoke_by_refresh_token(self, refresh_token: str) -> UUID | None:
        """仅当令牌仍是当前令牌时原子撤销会话。"""
        session_id = self.session_id_from_refresh_token(refresh_token)
        result = await cast(Any, self.redis.eval)(
            _REVOKE_REFRESH_TOKEN_SCRIPT,
            1,
            self._session_key(session_id),
            _hash_refresh_token(refresh_token),
        )
        if not result or int(result[0]) != 1:
            return None
        return UUID(str(result[1]))

    @staticmethod
    def session_id_from_refresh_token(refresh_token: str) -> str:
        """从刷新令牌提取会话 ID；格式不合法时统一视为无效令牌。"""
        parts = refresh_token.split(".")
        if len(parts) != 3 or parts[0] != "v1":
            raise InvalidRefreshToken("刷新令牌格式无效")
        try:
            session_id = str(UUID(parts[1]))
        except (ValueError, AttributeError) as exc:
            raise InvalidRefreshToken("刷新令牌格式无效") from exc
        if not parts[2]:
            raise InvalidRefreshToken("刷新令牌格式无效")
        return session_id

    def _session_key(self, session_id: str) -> str:
        return f"{self.key_prefix}auth:session:{session_id}"

    @staticmethod
    def _new_refresh_token(session_id: str) -> str:
        return f"v1.{session_id}.{secrets.token_urlsafe(48)}"

    @staticmethod
    def _to_mapping(session: AuthSession) -> dict[str, str]:
        return {
            "user_id": str(session.user_id),
            "session_family": session.session_family,
            "status": session.status,
            "refresh_token_hash": session.refresh_token_hash,
            "created_at": session.created_at.isoformat(),
            "last_rotated_at": session.last_rotated_at.isoformat(),
        }

    @staticmethod
    def _from_mapping(session_id: str, mapping: dict[str, str]) -> AuthSession:
        return AuthSession(
            session_id=session_id,
            user_id=UUID(mapping["user_id"]),
            session_family=mapping["session_family"],
            status=mapping["status"],
            refresh_token_hash=mapping["refresh_token_hash"],
            created_at=datetime.fromisoformat(mapping["created_at"]),
            last_rotated_at=datetime.fromisoformat(mapping["last_rotated_at"]),
        )


def _as_utc(value: datetime | None) -> datetime:
    current_time = value or datetime.now(UTC)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)
    return current_time.astimezone(UTC)


def _hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


__all__ = [
    "AuthSession",
    "CreatedSession",
    "InvalidRefreshToken",
    "RedisSessionStore",
]
