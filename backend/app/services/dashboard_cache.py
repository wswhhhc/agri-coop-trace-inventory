from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from app.infrastructure.cache import JsonCache


class DashboardCache:
    """大屏短时缓存；缓存不可用时由调用方继续查询数据库。"""

    def __init__(self, redis: Any, *, key_prefix: str, ttl_seconds: int) -> None:
        self._cache = JsonCache(
            redis,
            key_prefix=key_prefix,
            ttl_seconds=ttl_seconds,
            name="dashboard",
        )
        self.key_prefix = key_prefix

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
        digest = self._cache_key_digest(scope)
        return f"{self.key_prefix}dashboard:{endpoint}:{digest}"

    async def get(self, key: str) -> Any | None:
        return await self._cache.get(key)

    async def set(self, key: str, payload: Mapping[str, Any] | list[Any]) -> None:
        await self._cache.set(key, payload)

    async def delete(self, key: str) -> None:
        await self._cache.delete(key)

    @staticmethod
    def _cache_key_digest(scope: Mapping[str, Any]) -> str:
        import hashlib
        import json

        return hashlib.sha256(
            json.dumps(scope, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).hexdigest()


__all__ = ["DashboardCache"]
