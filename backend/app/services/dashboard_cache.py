from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from redis.exceptions import RedisError


class DashboardCache:
    """大屏短时缓存；缓存不可用时由调用方继续查询数据库。"""

    def __init__(self, redis: Any, *, key_prefix: str, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("大屏缓存 TTL 必须大于 0")
        self.redis = redis
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds

    def key(
        self,
        endpoint: str,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        filters: Mapping[str, Any],
    ) -> str:
        scope = {
            "cooperative": str(cooperative_id) if cooperative_id else "global",
            "warehouses": sorted(str(item) for item in warehouse_ids)
            if warehouse_ids is not None
            else "all",
            "filters": dict(sorted(filters.items())),
        }
        digest = hashlib.sha256(
            json.dumps(scope, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).hexdigest()
        return f"{self.key_prefix}dashboard:{endpoint}:{digest}"

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self.redis.get(key)
        except (RedisError, OSError, RuntimeError):
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            await self.delete(key)
            return None

    async def set(self, key: str, payload: Mapping[str, Any] | list[Any]) -> None:
        try:
            await self.redis.set(
                key,
                json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str),
                ex=self.ttl_seconds,
            )
        except (RedisError, OSError, RuntimeError):
            return

    async def delete(self, key: str) -> None:
        try:
            await self.redis.delete(key)
        except (RedisError, OSError, RuntimeError):
            return


__all__ = ["DashboardCache"]
