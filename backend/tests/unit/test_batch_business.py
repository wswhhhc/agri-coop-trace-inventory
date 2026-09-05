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
from app.models import (
    Cooperative,
    Permission,
    Product,
    ProductCategory,
    Role,
    User,
    UserWarehouse,
    Warehouse,
)

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
    user_id,
    role_code: str,
    cooperative_id,
    permissions: frozenset[str],
    warehouse_ids,
) -> AuthContext:
    return AuthContext(
        user_id=user_id,
        username="operator",
        real_name="操作员",
        role_code=role_code,
        permission_codes=permissions,
        cooperative_id=cooperative_id,
        warehouse_ids=warehouse_ids,
        session_id="session-1",
        token_id="token-1",
    )


@pytest_asyncio.fixture
async def batch_api(postgres_session_factory):
    async with postgres_session_factory() as session:
        permission = Permission(
            code="batch:manage",
            name="管理批次",
            module="batch",
        )
        admin_role = Role(
            code="COOPERATIVE_ADMIN",
            name="合作社管理员",
            permissions=[permission],
        )
        staff_role = Role(
            code="WAREHOUSE_STAFF",
            name="仓库工作人员",
            permissions=[permission],
        )
        first_cooperative = Cooperative(code="COOP-ONE", name="第一合作社")
        second_cooperative = Cooperative(code="COOP-TWO", name="第二合作社")
        first_category = ProductCategory(
            cooperative=first_cooperative,
            code="VEGETABLE",
            name="蔬菜",
        )
        second_category = ProductCategory(
            cooperative=second_cooperative,
            code="FRUIT",
            name="水果",
        )
        active_product = Product(
            cooperative=first_cooperative,
            category=first_category,
            code="TOMATO",
            name="番茄",
            unit="KG",
            shelf_life_days=7,
            safety_stock=10,
        )
        inactive_product = Product(
            cooperative=first_cooperative,
            category=first_category,
            code="OLD-TOMATO",
            name="停用番茄",
            unit="KG",
            shelf_life_days=7,
            safety_stock=10,
            is_active=False,
        )
        other_product = Product(
            cooperative=second_cooperative,
            category=second_category,
            code="APPLE",
            name="苹果",
            unit="KG",
            shelf_life_days=14,
            safety_stock=20,
        )
        warehouse = Warehouse(
            cooperative=first_cooperative,
            code="WH-ONE",
            name="一号仓库",
        )
        admin = User(
            cooperative=first_cooperative,
            role=admin_role,
            username="coop_admin",
            password_hash="not-used",
            real_name="合作社管理员",
        )
        staff = User(
            cooperative=first_cooperative,
            role=staff_role,
            username="warehouse_staff",
            password_hash="not-used",
            real_name="仓库工作人员",
        )
        session.add_all(
            [
                permission,
                admin_role,
                staff_role,
                first_cooperative,
                second_cooperative,
                first_category,
                second_category,
                active_product,
                inactive_product,
                other_product,
                warehouse,
                admin,
                staff,
            ]
        )
        await session.flush()
        session.add(UserWarehouse(user=staff, warehouse=warehouse))
        await session.commit()
        ids = (
            first_cooperative.id,
            second_cooperative.id,
            active_product.id,
            inactive_product.id,
            other_product.id,
            warehouse.id,
            admin.id,
            staff.id,
        )

    current_context = _context(
        user_id=ids[6],
        role_code="COOPERATIVE_ADMIN",
        cooperative_id=ids[0],
        permissions=frozenset({"batch:manage"}),
        warehouse_ids=frozenset(),
    )

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
async def test_cooperative_admin_can_create_list_read_and_change_batch_status(batch_api):
    client, cooperative_id, _, product_id, _, _, _, admin_id, _, _, _ = batch_api

    created = await client.post(
        "/api/v1/batches",
        json={
            "productId": str(product_id),
            "batchNo": "BATCH-001",
            "origin": "第一基地",
            "productionDate": "2026-09-05",
            "expiryDate": "2026-09-12",
            "responsiblePerson": "张三",
        },
    )
    assert created.status_code == 201
    data = created.json()["data"]
    batch_id = data["id"]
    assert data["cooperativeId"] == str(cooperative_id)
    assert data["createdBy"] == str(admin_id)
    assert data["traceCode"].startswith("tr_")
    assert data["status"] == "CREATED"

    listed = await client.get("/api/v1/batches?pageSize=10")
    assert listed.status_code == 200
    assert listed.json()["pagination"]["totalItems"] == 1
    assert (await client.get(f"/api/v1/batches/{batch_id}")).status_code == 200

    blocked = await client.patch(
        f"/api/v1/batches/{batch_id}",
        json={"status": "BLOCKED"},
    )
    assert blocked.status_code == 200
    assert blocked.json()["data"]["status"] == "BLOCKED"

    restored = await client.patch(
        f"/api/v1/batches/{batch_id}",
        json={"status": "CREATED"},
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["status"] == "CREATED"


@pytest.mark.asyncio
async def test_batch_rejects_inactive_or_cross_cooperative_product(batch_api):
    client, _, _, _, inactive_product_id, other_product_id, _, _, _, _, _ = batch_api

    inactive = await client.post(
        "/api/v1/batches",
        json={
            "productId": str(inactive_product_id),
            "batchNo": "BATCH-INACTIVE",
            "origin": "基地",
            "productionDate": "2026-09-05",
            "expiryDate": "2026-09-12",
        },
    )
    assert inactive.status_code == 409
    assert inactive.json()["error"]["code"] == "PRODUCT_DISABLED"

    cross = await client.post(
        "/api/v1/batches",
        json={
            "productId": str(other_product_id),
            "batchNo": "BATCH-CROSS",
            "origin": "基地",
            "productionDate": "2026-09-05",
            "expiryDate": "2026-09-12",
        },
    )
    assert cross.status_code == 404
    assert cross.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    unauthorized_warehouse = await client.get(
        f"/api/v1/batches?warehouseId={uuid4()}"
    )
    assert unauthorized_warehouse.status_code == 404


@pytest.mark.asyncio
async def test_batch_enforces_unique_no_date_order_and_status_transition(batch_api):
    client, _, _, product_id, _, _, _, _, _, _, _ = batch_api
    payload = {
        "productId": str(product_id),
        "batchNo": "BATCH-DUPLICATE",
        "origin": "基地",
        "productionDate": "2026-09-05",
        "expiryDate": "2026-09-12",
    }
    first = await client.post("/api/v1/batches", json=payload)
    assert first.status_code == 201
    duplicate = await client.post("/api/v1/batches", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "UNIQUE_CONFLICT"

    invalid_dates = await client.post(
        "/api/v1/batches",
        json={
            **payload,
            "batchNo": "BATCH-DATE",
            "productionDate": "2026-09-12",
            "expiryDate": "2026-09-05",
        },
    )
    assert invalid_dates.status_code == 422
    assert invalid_dates.json()["error"]["code"] == "VALIDATION_ERROR"

    batch_id = first.json()["data"]["id"]
    await client.patch(f"/api/v1/batches/{batch_id}", json={"status": "IN_STOCK"})
    depleted = await client.patch(
        f"/api/v1/batches/{batch_id}",
        json={"status": "DEPLETED"},
    )
    assert depleted.status_code == 200
    invalid_transition = await client.patch(
        f"/api/v1/batches/{batch_id}",
        json={"status": "CREATED"},
    )
    assert invalid_transition.status_code == 409
    assert invalid_transition.json()["error"]["code"] == "INVALID_BATCH_STATUS"


@pytest.mark.asyncio
async def test_warehouse_staff_requires_an_authorized_warehouse_and_cannot_cross_scope(
    batch_api,
):
    client, cooperative_id, _, product_id, _, other_product_id, warehouse_id, _, staff_id, set_context, _ = batch_api
    set_context(
        _context(
            user_id=staff_id,
            role_code="WAREHOUSE_STAFF",
            cooperative_id=cooperative_id,
            permissions=frozenset({"batch:manage"}),
            warehouse_ids=frozenset({warehouse_id}),
        )
    )

    created = await client.post(
        "/api/v1/batches",
        json={
            "productId": str(product_id),
            "batchNo": "BATCH-STAFF",
            "origin": "基地",
            "productionDate": "2026-09-05",
            "expiryDate": "2026-09-12",
        },
    )
    assert created.status_code == 201

    cross = await client.post(
        "/api/v1/batches",
        json={
            "productId": str(other_product_id),
            "batchNo": "BATCH-OTHER",
            "origin": "基地",
            "productionDate": "2026-09-05",
            "expiryDate": "2026-09-12",
        },
    )
    assert cross.status_code == 404
    assert cross.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    set_context(
        _context(
            user_id=staff_id,
            role_code="WAREHOUSE_STAFF",
            cooperative_id=cooperative_id,
            permissions=frozenset({"batch:manage"}),
            warehouse_ids=frozenset(),
        )
    )
    no_warehouse = await client.get("/api/v1/batches?pageSize=10")
    assert no_warehouse.status_code == 200
    assert no_warehouse.json()["data"] == []

    no_warehouse_create = await client.post(
        "/api/v1/batches",
        json={
            "productId": str(product_id),
            "batchNo": "BATCH-NO-WAREHOUSE",
            "origin": "基地",
            "productionDate": "2026-09-05",
            "expiryDate": "2026-09-12",
        },
    )
    assert no_warehouse_create.status_code == 404

    other_scope = await client.get(f"/api/v1/batches/{uuid4()}")
    assert other_scope.status_code == 404
