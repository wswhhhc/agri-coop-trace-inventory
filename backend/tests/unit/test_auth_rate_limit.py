from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from app.core.auth.rate_limit import LoginRateLimiter, RateLimitExceeded
from app.core.config import Settings
from app.infrastructure.redis import create_redis_client
from redis.exceptions import RedisError


def _settings(prefix: str) -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
        redis_url="redis://localhost:6379/13",
        redis_key_prefix=prefix,
        redis_socket_timeout_seconds=1,
        redis_max_connections=5,
        login_rate_limit_per_minute=2,
    )


@pytest_asyncio.fixture
async def login_limiter() -> LoginRateLimiter:
    settings = _settings(f"test-auth-limit-{uuid4().hex}:")
    redis = create_redis_client(settings)
    try:
        await redis.ping()
    except RedisError:
        await redis.aclose()
        pytest.skip("Redis 未运行，跳过登录限流集成测试")

    limiter = LoginRateLimiter(
        redis,
        key_prefix=settings.redis_key_prefix,
        max_attempts=settings.login_rate_limit_per_minute,
    )
    try:
        yield limiter
    finally:
        keys = await redis.keys(f"{settings.redis_key_prefix}*")
        if keys:
            await redis.delete(*keys)
        await redis.aclose()


@pytest.mark.asyncio
async def test_login_rate_limiter_blocks_after_configured_failures(
    login_limiter: LoginRateLimiter,
) -> None:
    await login_limiter.ensure_allowed("coop_admin", "127.0.0.1")
    await login_limiter.record_failure("coop_admin", "127.0.0.1")
    await login_limiter.record_failure("coop_admin", "127.0.0.1")

    with pytest.raises(RateLimitExceeded) as error:
        await login_limiter.ensure_allowed("coop_admin", "127.0.0.1")

    assert error.value.retry_after >= 1


@pytest.mark.asyncio
async def test_login_rate_limiter_tracks_account_and_ip_separately(
    login_limiter: LoginRateLimiter,
) -> None:
    await login_limiter.record_failure("first", "127.0.0.1")
    await login_limiter.record_failure("second", "127.0.0.1")

    with pytest.raises(RateLimitExceeded):
        await login_limiter.ensure_allowed("third", "127.0.0.1")


@pytest.mark.asyncio
async def test_login_rate_limiter_resets_account_after_success(
    login_limiter: LoginRateLimiter,
) -> None:
    await login_limiter.record_failure("coop_admin", "127.0.0.1")
    await login_limiter.reset_account("coop_admin")

    await login_limiter.record_failure("coop_admin", "192.0.2.1")
    await login_limiter.ensure_allowed("coop_admin", "192.0.2.1")
