from __future__ import annotations

from uuid import uuid4

import pytest
from app.core.auth.context import AuthContext
from app.schemas.common import ApiResponse
from app.services.query_cache import QueryCache


class MemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int,
        nx: bool = False,
    ) -> bool:
        if nx and key in self.values:
            return False
        self.values[key] = value
        self.ttls[key] = ex
        return True

    async def delete(self, key: str) -> int:
        existed = key in self.values
        self.values.pop(key, None)
        self.ttls.pop(key, None)
        return int(existed)

    async def eval(self, script: str, numkeys: int, key: str, token: str) -> int:
        if self.values.get(key) != token:
            return 0
        await self.delete(key)
        return 1

    async def scan_iter(self, *, match: str, count: int):
        for key in list(self.values):
            if key.startswith(match.removesuffix("*")):
                yield key


def _context(cooperative_id=None, warehouse_ids=None) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="cache-user",
        real_name="缓存用户",
        role_code="COOPERATIVE_ADMIN",
        permission_codes=frozenset(),
        cooperative_id=cooperative_id or uuid4(),
        warehouse_ids=warehouse_ids,
        session_id="session",
        token_id="token",
    )


@pytest.mark.asyncio
async def test_query_cache_round_trips_schema_and_scope_key() -> None:
    redis = MemoryRedis()
    cache = QueryCache(redis, key_prefix="agri:", ttl_seconds=300)
    context = _context(warehouse_ids=frozenset({uuid4()}))
    key = cache.key("product-detail", context, {"id": "product-1"})

    await cache.set(key, ApiResponse(data={"id": "product-1"}))

    cached = await cache.get(key, ApiResponse[dict[str, str]])

    assert cached is not None
    assert cached.data == {"id": "product-1"}
    assert key.startswith("agri:query:product-detail:")


@pytest.mark.asyncio
async def test_query_cache_rebuilds_once_and_invalidates_scope() -> None:
    redis = MemoryRedis()
    cache = QueryCache(redis, key_prefix="agri:", ttl_seconds=300)
    context = _context()
    key = cache.key("product-list", context, {"page": 1})
    calls = 0

    async def loader() -> ApiResponse[dict[str, str]]:
        nonlocal calls
        calls += 1
        return ApiResponse(data={"id": "product-1"})

    first = await cache.get_or_set(key, ApiResponse[dict[str, str]], loader)
    second = await cache.get_or_set(key, ApiResponse[dict[str, str]], loader)

    assert first == second
    assert calls == 1
    await cache.invalidate_resource("product-list", context.cooperative_id)
    assert await cache.get(key, ApiResponse[dict[str, str]]) is None


def test_query_cache_rejects_invalid_ttl() -> None:
    with pytest.raises(ValueError):
        QueryCache(MemoryRedis(), key_prefix="agri:", ttl_seconds=0)
