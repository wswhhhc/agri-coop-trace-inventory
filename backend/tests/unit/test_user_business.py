from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from app.core.auth.context import AuthContext
from app.core.auth.dependencies import get_auth_context
from app.core.config import Settings
from app.core.security import verify_password
from app.infrastructure.database import get_db_session
from app.main import create_app
from app.models import Cooperative, Permission, Role, User, UserWarehouse, Warehouse
from sqlalchemy import select

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
    permissions: frozenset[str] = frozenset({"user:manage"}),
    cooperative_id=None,
) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="operator",
        real_name="操作员",
        role_code=role_code,
        permission_codes=permissions,
        cooperative_id=cooperative_id,
        warehouse_ids=None if role_code == "SYSTEM_ADMIN" else frozenset(),
        session_id="session-1",
        token_id="token-1",
    )


@pytest_asyncio.fixture
async def user_api(postgres_session_factory):
    async with postgres_session_factory() as session:
        permission = Permission(
            code="user:manage",
            name="管理用户",
            module="identity",
        )
        system_role = Role(code="SYSTEM_ADMIN", name="系统管理员")
        cooperative_role = Role(
            code="COOPERATIVE_ADMIN",
            name="合作社管理员",
            permissions=[permission],
        )
        staff_role = Role(code="WAREHOUSE_STAFF", name="仓库工作人员")
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
                permission,
                system_role,
                cooperative_role,
                staff_role,
                first_cooperative,
                second_cooperative,
                first_warehouse,
                second_warehouse,
                other_warehouse,
            ]
        )
        await session.commit()
        ids = (
            first_cooperative.id,
            second_cooperative.id,
            first_warehouse.id,
            second_warehouse.id,
            other_warehouse.id,
        )

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
        yield client, *ids, set_context, postgres_session_factory


@pytest.mark.asyncio
async def test_system_admin_can_create_user_and_return_one_time_initial_password(
    user_api,
):
    client, cooperative_id, _, warehouse_id, _, _, _, session_factory = user_api

    created = await client.post(
        "/api/v1/users",
        json={
            "username": "warehouse_01",
            "displayName": "一号仓库员",
            "role": "WAREHOUSE_STAFF",
            "cooperativeId": str(cooperative_id),
            "warehouseIds": [str(warehouse_id)],
        },
    )

    assert created.status_code == 201
    data = created.json()["data"]
    assert data["username"] == "warehouse_01"
    assert data["role"] == "WAREHOUSE_STAFF"
    assert data["warehouseIds"] == [str(warehouse_id)]
    assert len(data["initialPassword"]) >= 10

    listed = await client.get("/api/v1/users?pageSize=10")
    assert listed.status_code == 200
    assert listed.json()["pagination"]["totalItems"] == 1

    updated = await client.patch(
        f"/api/v1/users/{data['id']}",
        json={"displayName": "更新后的仓库员", "phone": "13800138000"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["displayName"] == "更新后的仓库员"

    reset = await client.post(f"/api/v1/users/{data['id']}/password-resets")
    assert reset.status_code == 200
    temporary_password = reset.json()["data"]["temporaryPassword"]
    assert temporary_password != data["initialPassword"]

    async with session_factory() as session:
        user = await session.scalar(
            select(User).where(User.username == "warehouse_01")
        )
        assert user is not None
        assert verify_password(temporary_password, user.password_hash)
        assert await session.scalar(
            select(UserWarehouse).where(UserWarehouse.user_id == user.id)
        ) is not None


@pytest.mark.asyncio
async def test_cooperative_admin_is_limited_to_own_users_and_warehouses(user_api):
    client, cooperative_id, other_cooperative_id, first_warehouse_id, second_warehouse_id, other_warehouse_id, set_context, _ = user_api
    set_context(
        _context(
            role_code="COOPERATIVE_ADMIN",
            cooperative_id=cooperative_id,
        )
    )

    created = await client.post(
        "/api/v1/users",
        json={
            "username": "staff_01",
            "displayName": "仓库员工",
            "role": "WAREHOUSE_STAFF",
            "cooperativeId": str(cooperative_id),
            "warehouseIds": [str(first_warehouse_id)],
        },
    )
    assert created.status_code == 201
    user_id = created.json()["data"]["id"]

    own = await client.get(f"/api/v1/users/{user_id}")
    assert own.status_code == 200

    unauthorized_warehouse = await client.put(
        f"/api/v1/users/{user_id}/warehouses",
        json={"warehouseIds": [str(other_warehouse_id)]},
    )
    assert unauthorized_warehouse.status_code == 404
    assert unauthorized_warehouse.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    authorized_warehouses = await client.put(
        f"/api/v1/users/{user_id}/warehouses",
        json={"warehouseIds": [str(second_warehouse_id)]},
    )
    assert authorized_warehouses.status_code == 200
    assert authorized_warehouses.json()["data"]["warehouseIds"] == [
        str(second_warehouse_id)
    ]

    other_user = await client.post(
        "/api/v1/users",
        json={
            "username": "staff_02",
            "displayName": "其他合作社员工",
            "role": "WAREHOUSE_STAFF",
            "cooperativeId": str(other_cooperative_id),
        },
    )
    assert other_user.status_code == 404


@pytest.mark.asyncio
async def test_cooperative_admin_cannot_assign_system_admin_or_missing_permission_returns_403(
    user_api,
):
    client, cooperative_id, _, _, _, _, set_context, _ = user_api
    set_context(_context(role_code="COOPERATIVE_ADMIN", cooperative_id=cooperative_id))

    elevated = await client.post(
        "/api/v1/users",
        json={
            "username": "cannot_be_system",
            "displayName": "越权用户",
            "role": "SYSTEM_ADMIN",
        },
    )
    assert elevated.status_code == 403
    assert elevated.json()["error"]["code"] == "PERMISSION_DENIED"

    set_context(
        _context(
            role_code="WAREHOUSE_STAFF",
            permissions=frozenset(),
            cooperative_id=cooperative_id,
        )
    )
    denied = await client.get("/api/v1/users")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
