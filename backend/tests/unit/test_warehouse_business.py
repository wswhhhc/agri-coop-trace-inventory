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
from app.models import Cooperative, Warehouse

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
    permissions: frozenset[str] = frozenset({"warehouse:manage"}),
    cooperative_id=None,
    warehouse_ids=None,
) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="tester",
        real_name="测试用户",
        role_code=role_code,
        permission_codes=permissions,
        cooperative_id=cooperative_id,
        warehouse_ids=warehouse_ids,
        session_id="session-1",
        token_id="token-1",
    )


@pytest_asyncio.fixture
async def warehouse_api(postgres_session_factory):
    async with postgres_session_factory() as session:
        first_cooperative = Cooperative(code="COOP-ONE", name="第一合作社")
        second_cooperative = Cooperative(code="COOP-TWO", name="第二合作社")
        first_warehouse = Warehouse(
            cooperative=first_cooperative,
            code="WH-ONE",
            name="一号仓库",
        )
        second_warehouse = Warehouse(
            cooperative=first_cooperative,
            code="WH-TWO",
            name="二号仓库",
        )
        other_warehouse = Warehouse(
            cooperative=second_cooperative,
            code="WH-OTHER",
            name="其他合作社仓库",
        )
        session.add_all(
            [
                first_cooperative,
                second_cooperative,
                first_warehouse,
                second_warehouse,
                other_warehouse,
            ]
        )
        await session.commit()
        first_cooperative_id = first_cooperative.id
        first_warehouse_id = first_warehouse.id
        second_warehouse_id = second_warehouse.id
        other_warehouse_id = other_warehouse.id

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
        yield (
            client,
            first_cooperative_id,
            first_warehouse_id,
            second_warehouse_id,
            other_warehouse_id,
            set_context,
        )


@pytest.mark.asyncio
async def test_cooperative_admin_can_list_create_and_update_own_warehouses(
    warehouse_api,
):
    client, cooperative_id, first_id, _, _, set_context = warehouse_api
    set_context(
        _context(
            role_code="COOPERATIVE_ADMIN",
            cooperative_id=cooperative_id,
            warehouse_ids=frozenset(),
        )
    )

    listed = await client.get("/api/v1/warehouses?pageSize=10")
    assert listed.status_code == 200
    assert {item["code"] for item in listed.json()["data"]} == {
        "WH-ONE",
        "WH-TWO",
    }

    created = await client.post(
        "/api/v1/warehouses",
        json={"code": "WH-THREE", "name": "三号仓库"},
    )
    assert created.status_code == 201
    created_id = created.json()["data"]["id"]

    updated = await client.patch(
        f"/api/v1/warehouses/{first_id}",
        json={"name": "更新后的一号仓库", "status": "INACTIVE"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "更新后的一号仓库"
    assert updated.json()["data"]["status"] == "INACTIVE"
    assert (await client.get(f"/api/v1/warehouses/{created_id}")).status_code == 200


@pytest.mark.asyncio
async def test_warehouse_staff_can_only_read_authorized_warehouse(warehouse_api):
    client, cooperative_id, first_id, second_id, other_id, set_context = warehouse_api
    set_context(
        _context(
            role_code="WAREHOUSE_STAFF",
            permissions=frozenset(),
            cooperative_id=cooperative_id,
            warehouse_ids=frozenset({first_id}),
        )
    )

    listed = await client.get("/api/v1/warehouses?pageSize=10")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [str(first_id)]
    assert (await client.get(f"/api/v1/warehouses/{first_id}")).status_code == 200

    for warehouse_id in (second_id, other_id):
        response = await client.get(f"/api/v1/warehouses/{warehouse_id}")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_missing_warehouse_permission_returns_403(warehouse_api):
    client, cooperative_id, _, _, _, set_context = warehouse_api
    set_context(
        _context(
            role_code="WAREHOUSE_STAFF",
            permissions=frozenset(),
            cooperative_id=cooperative_id,
            warehouse_ids=frozenset(),
        )
    )

    response = await client.post(
        "/api/v1/warehouses",
        json={"code": "WH-NO-PERM", "name": "无权限仓库"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
