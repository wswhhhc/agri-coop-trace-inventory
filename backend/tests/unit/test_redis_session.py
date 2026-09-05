from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from app.core.auth.session import InvalidRefreshToken, RedisSessionStore
from app.core.config import Settings
from app.infrastructure.redis import create_redis_client
from redis.exceptions import RedisError


def _settings(prefix: str) -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret",
        postgres_password="unit-test-password",
        redis_url="redis://localhost:6379/15",
        redis_key_prefix=prefix,
        redis_socket_timeout_seconds=1,
        redis_max_connections=5,
        refresh_token_expire_days=1,
    )


@pytest_asyncio.fixture
async def session_store() -> RedisSessionStore:
    settings = _settings(f"test-auth-{uuid4().hex}:")
    client = create_redis_client(settings)
    try:
        await client.ping()
    except RedisError:
        await client.aclose()
        pytest.skip("Redis 未运行，跳过 Redis 会话集成测试")

    store = RedisSessionStore(
        client,
        key_prefix=settings.redis_key_prefix,
        ttl_seconds=settings.refresh_token_expire_days * 24 * 60 * 60,
    )
    try:
        yield store
    finally:
        keys = await client.keys(f"{settings.redis_key_prefix}*")
        if keys:
            await client.delete(*keys)
        await client.aclose()


@pytest.mark.asyncio
async def test_session_store_creates_and_reads_ttl_bound_session(
    session_store: RedisSessionStore,
) -> None:
    user_id = uuid4()

    created = await session_store.create(user_id)
    session = created.session
    refresh_token = created.refresh_token
    loaded = await session_store.get(session.session_id)

    assert session.user_id == user_id
    assert session.status == "ACTIVE"
    assert refresh_token.startswith(f"v1.{session.session_id}.")
    assert loaded == session
    assert await session_store.ttl(session.session_id) > 0


@pytest.mark.asyncio
async def test_session_store_rotates_refresh_token_and_invalidates_old_token(
    session_store: RedisSessionStore,
) -> None:
    created = await session_store.create(uuid4())
    session = created.session
    old_refresh_token = created.refresh_token

    rotated = await session_store.rotate(old_refresh_token)
    rotated_session = rotated.session
    new_refresh_token = rotated.refresh_token

    assert rotated_session.session_id == session.session_id
    assert new_refresh_token != old_refresh_token
    second_rotation = await session_store.rotate(new_refresh_token)
    assert second_rotation.session.session_id == session.session_id
    with pytest.raises(InvalidRefreshToken):
        await session_store.rotate(old_refresh_token)


@pytest.mark.asyncio
async def test_session_store_revoke_makes_refresh_token_unusable(
    session_store: RedisSessionStore,
) -> None:
    created = await session_store.create(uuid4())
    session = created.session
    refresh_token = created.refresh_token

    await session_store.revoke(session.session_id)

    assert await session_store.get(session.session_id) is None
    with pytest.raises(InvalidRefreshToken):
        await session_store.rotate(refresh_token)


@pytest.mark.asyncio
async def test_revoke_by_refresh_token_requires_current_token(
    session_store: RedisSessionStore,
) -> None:
    created = await session_store.create(uuid4())
    rotated = await session_store.rotate(created.refresh_token)

    assert await session_store.revoke_by_refresh_token(created.refresh_token) is None
    assert await session_store.get(created.session.session_id) is not None

    revoked_user_id = await session_store.revoke_by_refresh_token(rotated.refresh_token)

    assert revoked_user_id == created.session.user_id
    assert await session_store.get(created.session.session_id) is None
