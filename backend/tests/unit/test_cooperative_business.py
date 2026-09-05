from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from app.core.auth.context import AuthContext
from app.core.auth.dependencies import get_auth_context
from app.core.config import Settings
from app.infrastructure.database import get_db_session
from app.main import create_app
from app.models import Cooperative, CooperativeStatus

pytestmark = pytest.mark.postgres


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
    )


def _context(
    *,
    role_code: str = "SYSTEM_ADMIN",
    permissions: frozenset[str] = frozenset({"cooperative:manage"}),
    cooperative_id=None,
) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="tester",
        real_name="测试用户",
        role_code=role_code,
        permission_codes=permissions,
        cooperative_id=cooperative_id,
        warehouse_ids=None if role_code == "SYSTEM_ADMIN" else frozenset(),
        session_id="session-1",
        token_id="token-1",
    )


@pytest_asyncio.fixture
async def cooperative_api(postgres_session_factory):
    async with postgres_session_factory() as session:
        first = Cooperative(code="COOP-ONE", name="第一合作社")
        second = Cooperative(code="COOP-TWO", name="第二合作社")
        session.add_all([first, second])
        await session.commit()
        first_id = first.id
        second_id = second.id

    current_context = _context()

    async def override_db_session():
        async with postgres_session_factory() as session:
            yield session

    async def override_auth_context() -> AuthContext:
        return current_context

    def set_context(context: AuthContext) -> None:
        nonlocal current_context
        current_context = context

    application = create_app(_settings())
    application.dependency_overrides[get_db_session] = override_db_session
    application.dependency_overrides[get_auth_context] = override_auth_context

    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, first_id, second_id, set_context


@pytest.mark.asyncio
async def test_system_admin_can_list_create_read_and_update_cooperatives(cooperative_api):
    client, first_id, _, _ = cooperative_api

    listed = await client.get("/api/v1/cooperatives?pageSize=10")
    assert listed.status_code == 200
    assert {item["code"] for item in listed.json()["data"]} == {
        "COOP-ONE",
        "COOP-TWO",
    }
    assert listed.json()["pagination"]["totalItems"] == 2

    created = await client.post(
        "/api/v1/cooperatives",
        json={
            "code": "COOP-THREE",
            "name": "第三合作社",
            "contactName": "张三",
            "contactPhone": "13800138000",
        },
    )
    assert created.status_code == 201
    created_id = created.json()["data"]["id"]

    detail = await client.get(f"/api/v1/cooperatives/{created_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["name"] == "第三合作社"

    updated = await client.patch(
        f"/api/v1/cooperatives/{first_id}",
        json={"name": "更新后的合作社", "status": "INACTIVE"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "更新后的合作社"
    assert updated.json()["data"]["status"] == CooperativeStatus.INACTIVE.value


@pytest.mark.asyncio
async def test_cooperative_admin_can_read_only_own_cooperative_and_cross_scope_is_404(
    cooperative_api,
):
    client, first_id, second_id, set_context = cooperative_api

    set_context(
        _context(
            role_code="COOPERATIVE_ADMIN",
            permissions=frozenset({"user:manage"}),
            cooperative_id=first_id,
        )
    )
    own = await client.get(f"/api/v1/cooperatives/{first_id}")
    other = await client.get(f"/api/v1/cooperatives/{second_id}")

    assert own.status_code == 200
    assert other.status_code == 404
    assert other.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_missing_cooperative_permission_returns_403(cooperative_api):
    client, _, _, set_context = cooperative_api
    set_context(
        _context(
            role_code="WAREHOUSE_STAFF",
            permissions=frozenset(),
        )
    )

    response = await client.post(
        "/api/v1/cooperatives",
        json={"code": "COOP-NO-PERM", "name": "无权限合作社"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_empty_cooperative_update_returns_400(cooperative_api):
    client, first_id, _, _ = cooperative_api

    response = await client.patch(f"/api/v1/cooperatives/{first_id}", json={})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


@pytest.mark.asyncio
async def test_duplicate_cooperative_code_returns_409(cooperative_api):
    client, _, _, _ = cooperative_api

    response = await client.post(
        "/api/v1/cooperatives",
        json={"code": "COOP-ONE", "name": "重复编码合作社"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "UNIQUE_CONFLICT"
