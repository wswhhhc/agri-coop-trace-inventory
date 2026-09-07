"""面向 API 查询响应的范围隔离缓存。"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel, ValidationError
from redis.exceptions import RedisError

from app.core.auth.context import AuthContext
from app.infrastructure.cache import CacheKeyBuilder, JsonCache

logger = logging.getLogger(__name__)
ModelT = TypeVar("ModelT", bound=BaseModel)


class QueryCache:
    """缓存 API Schema 响应，权限校验由调用方在查缓存前完成。"""

    def __init__(
        self,
        redis: Any,
        *,
        key_prefix: str,
        ttl_seconds: int,
        name: str = "query",
        jitter_ratio: float = 0.1,
    ) -> None:
        self._cache = JsonCache(
            redis,
            key_prefix=key_prefix,
            ttl_seconds=ttl_seconds,
            name=name,
            jitter_ratio=jitter_ratio,
        )
        self._keys = CacheKeyBuilder(key_prefix)
        self.key_prefix = key_prefix

    def key(
        self,
        resource: str,
        context: AuthContext,
        filters: Mapping[str, Any] | None = None,
    ) -> str:
        cooperative = str(context.cooperative_id) if context.cooperative_id else "global"
        scope = {
            "role": context.role_code,
            "cooperative": cooperative,
            "warehouses": context.warehouse_ids if context.warehouse_ids is not None else "all",
        }
        return self._keys.build(
            resource,
            namespace=cooperative,
            scope=scope,
            filters=filters,
        )

    async def get(self, key: str, model_type: type[ModelT]) -> ModelT | None:
        raw = await self._cache.get(key)
        if raw is None:
            return None
        try:
            return model_type.model_validate(raw)
        except ValidationError:
            await self._cache.delete(key)
            return None

    async def set(self, key: str, value: BaseModel, *, ttl_seconds: int | None = None) -> None:
        await self._cache.set(
            key,
            value.model_dump(mode="json", by_alias=True),
            ttl_seconds=ttl_seconds,
        )

    async def get_or_set(
        self,
        key: str,
        model_type: type[ModelT],
        loader: Callable[[], Awaitable[ModelT]],
        *,
        ttl_seconds: int | None = None,
    ) -> ModelT | None:
        cached = await self.get(key, model_type)
        if cached is not None:
            return cached

        async def load_payload() -> dict[str, Any]:
            value = await loader()
            return value.model_dump(mode="json", by_alias=True)

        raw = await self._cache.get_or_set(key, load_payload, ttl_seconds=ttl_seconds)
        try:
            return model_type.model_validate(raw)
        except (TypeError, ValueError, ValidationError):
            await self._cache.delete(key)
            return None

    async def invalidate_resource(
        self,
        resource: str,
        cooperative_id: UUID | None,
    ) -> None:
        namespace = str(cooperative_id) if cooperative_id else "global"
        try:
            namespaces = {namespace}
            if namespace != "global":
                # 系统管理员缓存覆盖全局数据，任一合作社变更都必须清除它。
                namespaces.add("global")
            for current_namespace in namespaces:
                pattern = f"{self.key_prefix}query:{resource}:{current_namespace}:*"
                async for key in self._scan(pattern):
                    await self._cache.delete(key)
        except (RedisError, OSError, RuntimeError):
            logger.warning("cache_event event=invalidate_error resource=%s", resource)

    async def _scan(self, pattern: str):
        scan_iter = self._cache.redis.scan_iter
        async for key in scan_iter(match=pattern, count=100):
            yield key


__all__ = ["QueryCache"]
