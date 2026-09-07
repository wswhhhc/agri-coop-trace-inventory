from __future__ import annotations

import asyncio

import pytest
from app.infrastructure.cache import CacheKeyBuilder, JsonCache
from redis.exceptions import RedisError


class MemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.set_calls: list[tuple[str, int | None, bool]] = []

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
        self.set_calls.append((key, ex, nx))
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


class BrokenRedis(MemoryRedis):
    async def get(self, key: str) -> str | None:
        raise RedisError("redis unavailable")

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int,
        nx: bool = False,
    ) -> bool:
        raise RedisError("redis unavailable")


def test_cache_key_builder_is_stable_and_scope_aware() -> None:
    builder = CacheKeyBuilder("agri:")
    first = builder.build(
        "product-list",
        scope={"cooperative": "coop-1", "warehouses": {"wh-2", "wh-1"}},
        filters={"page": 1, "pageSize": 20},
    )
    second = builder.build(
        "product-list",
        scope={"warehouses": {"wh-1", "wh-2"}, "cooperative": "coop-1"},
        filters={"pageSize": 20, "page": 1},
    )
    other_scope = builder.build(
        "product-list",
        scope={"cooperative": "coop-2", "warehouses": {"wh-1"}},
        filters={"page": 1, "pageSize": 20},
    )

    assert first == second
    assert first != other_scope
    assert first.startswith("agri:query:product-list:")


@pytest.mark.asyncio
async def test_json_cache_applies_ttl_jitter() -> None:
    redis = MemoryRedis()
    cache = JsonCache(
        redis,
        key_prefix="agri:",
        ttl_seconds=100,
        jitter_ratio=0.1,
        random_fn=lambda lower, upper: upper,
    )

    await cache.set("agri:key", {"count": 2})

    assert redis.set_calls == [("agri:key", 110, False)]
    assert await cache.get("agri:key") == {"count": 2}


@pytest.mark.asyncio
async def test_json_cache_handles_malformed_json_and_redis_failure() -> None:
    redis = MemoryRedis()
    redis.values["agri:bad"] = "{not-json"
    cache = JsonCache(redis, key_prefix="agri:", ttl_seconds=60)

    assert await cache.get("agri:bad") is None
    assert "agri:bad" not in redis.values

    broken = JsonCache(BrokenRedis(), key_prefix="agri:", ttl_seconds=60)
    assert await broken.get("agri:key") is None
    await broken.set("agri:key", {"count": 1})
    await broken.delete("agri:key")


@pytest.mark.asyncio
async def test_json_cache_allows_one_rebuilder_per_key() -> None:
    redis = MemoryRedis()
    cache = JsonCache(redis, key_prefix="agri:", ttl_seconds=60, lock_ttl_seconds=5)

    first = await cache.acquire_rebuild_lock("agri:key")
    second = await cache.acquire_rebuild_lock("agri:key")

    assert first is not None
    assert second is None
    assert await cache.release_rebuild_lock("agri:key", "wrong-token") is False
    assert await cache.release_rebuild_lock("agri:key", first) is True
    assert await cache.acquire_rebuild_lock("agri:key") is not None


@pytest.mark.asyncio
async def test_json_cache_get_or_set_rechecks_after_lock_wait() -> None:
    redis = MemoryRedis()
    cache = JsonCache(redis, key_prefix="agri:", ttl_seconds=60, lock_ttl_seconds=5)
    loader_calls = 0

    async def loader() -> dict[str, int]:
        nonlocal loader_calls
        loader_calls += 1
        await asyncio.sleep(0)
        return {"count": 3}

    value = await cache.get_or_set("agri:key", loader)

    assert value == {"count": 3}
    assert loader_calls == 1
    assert await cache.get("agri:key") == {"count": 3}
