from __future__ import annotations

from datetime import date
from decimal import Decimal
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
    Batch,
    BatchStatus,
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


def _context(*, user_id, role_code, cooperative_id, permissions, warehouse_ids):
    return AuthContext(
        user_id=user_id,
        username="inventory-operator",
        real_name="库存操作员",
        role_code=role_code,
        permission_codes=frozenset(permissions),
        cooperative_id=cooperative_id,
        warehouse_ids=warehouse_ids,
        session_id="inventory-session",
        token_id="inventory-token",
    )


@pytest_asyncio.fixture
async def inventory_api(postgres_session_factory):
    async with postgres_session_factory() as session:
        read = Permission(code="inventory:read", name="查看库存", module="inventory")
        write = Permission(code="inventory:write", name="操作库存", module="inventory")
        role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员", permissions=[read, write])
        staff_role = Role(code="WAREHOUSE_STAFF", name="仓库工作人员", permissions=[read, write])
        cooperative = Cooperative(code=f"inventory-{uuid4().hex[:8]}", name="库存合作社")
        category = ProductCategory(cooperative=cooperative, code="grain", name="粮食")
        product = Product(
            cooperative=cooperative,
            category=category,
            code="corn",
            name="玉米",
            unit="KG",
            shelf_life_days=365,
            safety_stock=Decimal("10.000"),
        )
        warehouse = Warehouse(cooperative=cooperative, code="WH-1", name="一号仓")
        second_warehouse = Warehouse(cooperative=cooperative, code="WH-2", name="二号仓")
        admin = User(
            cooperative=cooperative,
            role=role,
            username=f"inventory-admin-{uuid4().hex[:8]}",
            password_hash="not-used",
            real_name="管理员",
        )
        staff = User(
            cooperative=cooperative,
            role=staff_role,
            username=f"inventory-staff-{uuid4().hex[:8]}",
            password_hash="not-used",
            real_name="仓库员",
        )
        batch = Batch(
            cooperative=cooperative,
            product=product,
            batch_no=f"B-{uuid4().hex[:8]}",
            trace_code=f"T-{uuid4().hex[:8]}",
            origin="测试基地",
            production_date=date(2026, 9, 1),
            expiry_date=date(2027, 9, 1),
            status=BatchStatus.CREATED,
            creator=admin,
        )
        session.add_all([
            read,
            write,
            role,
            staff_role,
            cooperative,
            category,
            product,
            warehouse,
            second_warehouse,
            admin,
            staff,
            batch,
        ])
        await session.flush()
        session.add(UserWarehouse(user=staff, warehouse=warehouse))
        await session.commit()
        ids = cooperative.id, warehouse.id, second_warehouse.id, batch.id, admin.id, staff.id

    current = _context(
        user_id=ids[4],
        role_code="COOPERATIVE_ADMIN",
        cooperative_id=ids[0],
        permissions={"inventory:read", "inventory:write"},
        warehouse_ids=None,
    )

    async def override_db_session():
        async with postgres_session_factory() as session:
            yield session

    async def override_auth_context():
        return current

    def set_context(new_context: AuthContext) -> None:
        nonlocal current
        current = new_context

    application = create_app(_settings())
    application.dependency_overrides[get_db_session] = override_db_session
    application.dependency_overrides[get_auth_context] = override_auth_context
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, *ids, set_context


@pytest.mark.asyncio
async def test_inventory_receipt_issue_and_idempotency(inventory_api) -> None:
    client, _, warehouse_id, _, batch_id, _, _, _ = inventory_api
    receipt = {
        "warehouseId": str(warehouse_id),
        "batchId": str(batch_id),
        "quantity": "20.000",
        "occurredAt": "2026-09-06T10:00:00+08:00",
    }
    first = await client.post(
        "/api/v1/inventory-receipts",
        json=receipt,
        headers={"Idempotency-Key": "receipt-1"},
    )
    assert first.status_code == 201
    repeated = await client.post(
        "/api/v1/inventory-receipts",
        json=receipt,
        headers={"Idempotency-Key": "receipt-1"},
    )
    assert repeated.status_code == 201
    assert repeated.json()["data"]["transactionId"] == first.json()["data"]["transactionId"]

    insufficient = await client.post(
        "/api/v1/inventory-issues",
        json={
            "warehouseId": str(warehouse_id),
            "batchId": str(batch_id),
            "quantity": "21.000",
            "occurredAt": "2026-09-06T11:00:00+08:00",
        },
        headers={"Idempotency-Key": "issue-too-much"},
    )
    assert insufficient.status_code == 409
    assert insufficient.json()["error"]["code"] == "INSUFFICIENT_STOCK"

    issued = await client.post(
        "/api/v1/inventory-issues",
        json={
            "warehouseId": str(warehouse_id),
            "batchId": str(batch_id),
            "quantity": "5.000",
            "occurredAt": "2026-09-06T11:00:00+08:00",
        },
        headers={"Idempotency-Key": "issue-1"},
    )
    assert issued.status_code == 201
    listed = await client.get("/api/v1/inventories")
    assert listed.status_code == 200
    assert listed.json()["data"][0]["quantity"] == 15
    assert listed.json()["data"][0]["warehouse"]["id"] == str(warehouse_id)


@pytest.mark.asyncio
async def test_inventory_transfer_is_atomic_and_staff_scope_is_enforced(inventory_api) -> None:
    client, cooperative_id, warehouse_id, second_warehouse_id, batch_id, _, staff_id, _ = inventory_api
    await client.post(
        "/api/v1/inventory-receipts",
        json={
            "warehouseId": str(warehouse_id),
            "batchId": str(batch_id),
            "quantity": "12.000",
            "occurredAt": "2026-09-06T10:00:00+08:00",
        },
        headers={"Idempotency-Key": "transfer-receipt"},
    )
    transfer = await client.post(
        "/api/v1/stock-transfers",
        json={
            "sourceWarehouseId": str(warehouse_id),
            "targetWarehouseId": str(second_warehouse_id),
            "batchId": str(batch_id),
            "quantity": "7.000",
            "occurredAt": "2026-09-06T12:00:00+08:00",
        },
        headers={"Idempotency-Key": "transfer-1"},
    )
    assert transfer.status_code == 201
    transactions = await client.get("/api/v1/inventory-transactions")
    assert transactions.json()["pagination"]["totalItems"] == 3

    set_context = inventory_api[-1]
    set_context(
        _context(
            user_id=staff_id,
            role_code="WAREHOUSE_STAFF",
            cooperative_id=cooperative_id,
            permissions={"inventory:read", "inventory:write"},
            warehouse_ids=frozenset({warehouse_id}),
        )
    )
    scoped = await client.get("/api/v1/inventories")
    assert scoped.status_code == 200
    assert all(item["warehouse"]["id"] == str(warehouse_id) for item in scoped.json()["data"])
    forbidden_scope = await client.get(f"/api/v1/inventories?warehouseId={second_warehouse_id}")
    assert forbidden_scope.status_code == 404
