from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from app.core.audit.service import AuditLogService
from app.core.auth.dependencies import get_audit_log_service
from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.infrastructure.database import get_db_session, get_transactional_session
from app.infrastructure.redis import create_redis_client, get_redis_client
from app.main import create_app
from app.models import Cooperative, Role, User
from redis.exceptions import RedisError


def _settings(prefix: str) -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
        redis_url="redis://localhost:6379/14",
        redis_key_prefix=prefix,
        redis_socket_timeout_seconds=1,
        redis_max_connections=5,
        refresh_token_expire_days=1,
        refresh_token_cookie_samesite="strict",
        refresh_token_cookie_secure=False,
    )


@pytest_asyncio.fixture
async def auth_api(postgres_session_factory):
    settings = _settings(f"test-auth-api-{uuid4().hex}:")
    redis = create_redis_client(settings)
    try:
        await redis.ping()
    except RedisError:
        await redis.aclose()
        pytest.skip("Redis 未运行，跳过认证 API 集成测试")

    session_factory = postgres_session_factory
    async with postgres_session_factory() as session:
        role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
        cooperative = Cooperative(code="coop-api", name="API 合作社")
        user = User(
            cooperative=cooperative,
            role=role,
            username="coop_admin",
            password_hash=hash_password("correct-password"),
            real_name="合作社管理员",
        )
        session.add(user)
        await session.commit()

    async def override_transactional_session():
        async with session_factory() as session, session.begin():
            yield session

    async def override_db_session():
        async with session_factory() as session:
            yield session

    application = create_app(settings)
    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[get_redis_client] = lambda: redis
    application.dependency_overrides[get_transactional_session] = (
        override_transactional_session
    )
    application.dependency_overrides[get_db_session] = override_db_session
    application.dependency_overrides[get_audit_log_service] = (
        lambda: AuditLogService(session_factory)
    )
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            yield client
        finally:
            keys = await redis.keys(f"{settings.redis_key_prefix}*")
            if keys:
                await redis.delete(*keys)
            await redis.aclose()


@pytest.mark.asyncio
async def test_login_sets_configured_http_only_cookie_and_returns_access_token(auth_api):
    response = await auth_api.post(
        "/api/v1/auth/login",
        json={"username": "coop_admin", "password": "correct-password"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["tokenType"] == "Bearer"
    assert response.json()["data"]["user"]["username"] == "coop_admin"
    set_cookie = response.headers["set-cookie"]
    assert "HttpOnly" in set_cookie
    assert "SameSite=strict" in set_cookie
    assert "Path=/api/v1/auth" in set_cookie
    assert "Max-Age=86400" in set_cookie


@pytest.mark.asyncio
async def test_refresh_rotates_cookie_and_old_cookie_is_rejected(auth_api):
    login = await auth_api.post(
        "/api/v1/auth/login",
        json={"username": "coop_admin", "password": "correct-password"},
    )
    old_cookie = auth_api.cookies.get("refresh_token")

    refreshed = await auth_api.post("/api/v1/auth/refresh")

    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["accessToken"] != login.json()["data"]["accessToken"]
    new_cookie = auth_api.cookies.get("refresh_token")
    assert new_cookie != old_cookie

    auth_api.cookies.clear()
    auth_api.cookies.set("refresh_token", old_cookie, path="/api/v1/auth")
    old_refresh = await auth_api.post("/api/v1/auth/refresh")
    assert old_refresh.status_code == 401
    assert old_refresh.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


@pytest.mark.asyncio
async def test_me_returns_current_user_permissions_and_data_scope(auth_api):
    login = await auth_api.post(
        "/api/v1/auth/login",
        json={"username": "coop_admin", "password": "correct-password"},
    )
    access_token = login.json()["data"]["accessToken"]

    response = await auth_api.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["username"] == "coop_admin"
    assert response.json()["data"]["permissions"] == []
    assert response.json()["data"]["warehouseIds"] == []


@pytest.mark.asyncio
async def test_logout_clears_cookie_and_invalidates_session(auth_api):
    await auth_api.post(
        "/api/v1/auth/login",
        json={"username": "coop_admin", "password": "correct-password"},
    )
    refresh_cookie = auth_api.cookies.get("refresh_token")

    logout = await auth_api.post("/api/v1/auth/logout")

    assert logout.status_code == 204
    assert "Max-Age=0" in logout.headers["set-cookie"]

    refresh_again = await auth_api.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={refresh_cookie}"},
    )
    assert refresh_again.status_code == 401


@pytest.mark.asyncio
async def test_unknown_username_and_wrong_password_have_same_error(auth_api):
    unknown = await auth_api.post(
        "/api/v1/auth/login",
        json={"username": "unknown", "password": "wrong-password"},
    )
    wrong_password = await auth_api.post(
        "/api/v1/auth/login",
        json={"username": "coop_admin", "password": "wrong-password"},
    )

    assert unknown.status_code == wrong_password.status_code == 401
    assert unknown.json()["error"]["code"] == wrong_password.json()["error"]["code"]
    assert unknown.json()["error"]["message"] == wrong_password.json()["error"]["message"]
    assert unknown.json()["error"]["details"] == wrong_password.json()["error"]["details"]


@pytest.mark.asyncio
async def test_login_is_rate_limited_after_ten_failed_attempts(auth_api):
    for _ in range(10):
        response = await auth_api.post(
            "/api/v1/auth/login",
            json={"username": "coop_admin", "password": "wrong-password"},
        )
        assert response.status_code == 401

    blocked = await auth_api.post(
        "/api/v1/auth/login",
        json={"username": "coop_admin", "password": "wrong-password"},
    )

    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert int(blocked.headers["retry-after"]) >= 1
