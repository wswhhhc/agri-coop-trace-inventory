from __future__ import annotations

import re
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from app.core.auth.context import AuthContext
from app.core.auth.dependencies import get_auth_context
from app.core.config import Settings
from app.infrastructure.database import get_db_session
from app.main import create_app
from app.models import Cooperative, Product, ProductCategory, Warehouse
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
    role_code: str = "COOPERATIVE_ADMIN",
    permissions: frozenset[str] = frozenset({"product:manage"}),
    cooperative_id=None,
    warehouse_ids=None,
) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
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
async def product_api(postgres_session_factory):
    async with postgres_session_factory() as session:
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
        first_product = Product(
            cooperative=first_cooperative,
            category=first_category,
            code="TOMATO",
            name="番茄",
            unit="KG",
            shelf_life_days=7,
            safety_stock=10,
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
        session.add_all(
            [
                first_cooperative,
                second_cooperative,
                first_category,
                second_category,
                first_product,
                other_product,
                warehouse,
            ]
        )
        await session.commit()
        ids = (
            first_cooperative.id,
            second_cooperative.id,
            first_category.id,
            second_category.id,
            first_product.id,
            other_product.id,
            warehouse.id,
        )

    current_context = _context(cooperative_id=ids[0])

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
async def test_cooperative_admin_can_manage_categories_and_products(product_api):
    client, cooperative_id, _, _, _, _, _, _, _, session_factory = product_api

    category = await client.post(
        "/api/v1/product-categories",
        json={"code": "GRAIN", "name": "粮食", "description": "粮食类"},
    )
    assert category.status_code == 201
    category_id = category.json()["data"]["id"]

    listed_categories = await client.get(
        "/api/v1/product-categories?pageSize=10"
    )
    assert listed_categories.status_code == 200
    assert listed_categories.json()["pagination"]["totalItems"] == 2

    product = await client.post(
        "/api/v1/products",
        json={
            "categoryId": category_id,
            "code": "CORN",
            "name": "玉米",
            "unit": "KG",
            "shelfLifeDays": 365,
            "safetyStock": 500,
        },
    )
    assert product.status_code == 201
    product_id = product.json()["data"]["id"]
    assert product.json()["data"]["cooperativeId"] == str(cooperative_id)

    updated = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"safetyStock": 600, "isActive": False},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["safetyStock"] == 600.0
    assert updated.json()["data"]["isActive"] is False

    async with session_factory() as session:
        saved = await session.scalar(select(Product).where(Product.id == product_id))
        assert saved is not None
        assert saved.cooperative_id == cooperative_id


@pytest.mark.asyncio
async def test_product_code_is_generated_when_create_request_omits_it(product_api):
    client, _, _, category_id, _, _, _, _, _, _ = product_api
    payload = {
        "categoryId": str(category_id),
        "name": "新鲜玉米",
        "unit": "KG",
        "shelfLifeDays": 30,
        "safetyStock": 10,
    }

    first = await client.post("/api/v1/products", json=payload)
    second = await client.post("/api/v1/products", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    first_code = first.json()["data"]["code"]
    second_code = second.json()["data"]["code"]
    assert re.fullmatch(r"VEGETABLE-[A-Z0-9]{6}", first_code)
    assert re.fullmatch(r"VEGETABLE-[A-Z0-9]{6}", second_code)
    assert first_code != second_code


@pytest.mark.asyncio
async def test_product_queries_cannot_cross_cooperative_or_empty_warehouse_scope(
    product_api,
):
    client, cooperative_id, _, _, _, own_product_id, other_product_id, warehouse_id, set_context, _ = product_api
    set_context(
        _context(
            role_code="WAREHOUSE_STAFF",
            permissions=frozenset(),
            cooperative_id=cooperative_id,
            warehouse_ids=frozenset({warehouse_id}),
        )
    )

    listed = await client.get("/api/v1/products?pageSize=10")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [str(own_product_id)]
    assert (await client.get(f"/api/v1/products/{own_product_id}")).status_code == 200

    unauthorized_warehouse = await client.get(
        f"/api/v1/products?warehouseId={uuid4()}"
    )
    assert unauthorized_warehouse.status_code == 404

    other = await client.get(f"/api/v1/products/{other_product_id}")
    assert other.status_code == 404
    assert other.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    set_context(
        _context(
            role_code="WAREHOUSE_STAFF",
            permissions=frozenset(),
            cooperative_id=cooperative_id,
            warehouse_ids=frozenset(),
        )
    )
    empty = await client.get("/api/v1/products?pageSize=10")
    assert empty.status_code == 200
    assert empty.json()["data"] == []


@pytest.mark.asyncio
async def test_product_rejects_cross_cooperative_category_and_missing_permission(
    product_api,
):
    client, cooperative_id, _, _, second_category_id, _, _, _, set_context, _ = product_api

    cross_category = await client.post(
        "/api/v1/products",
        json={
            "categoryId": str(second_category_id),
            "code": "CROSS",
            "name": "跨合作社产品",
            "unit": "KG",
            "shelfLifeDays": 10,
            "safetyStock": 1,
        },
    )
    assert cross_category.status_code == 404

    set_context(
        _context(
            role_code="WAREHOUSE_STAFF",
            permissions=frozenset(),
            cooperative_id=cooperative_id,
        )
    )
    denied = await client.post(
        "/api/v1/products",
        json={
            "categoryId": str(second_category_id),
            "code": "NO-PERM",
            "name": "无权限产品",
            "unit": "KG",
            "shelfLifeDays": 10,
            "safetyStock": 1,
        },
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_product_schema_rejects_invalid_shelf_life_and_safety_stock(product_api):
    client, _, _, category_id, _, _, _, _, _, _ = product_api

    response = await client.post(
        "/api/v1/products",
        json={
            "categoryId": str(category_id),
            "code": "INVALID",
            "name": "非法产品",
            "unit": "KG",
            "shelfLifeDays": 0,
            "safetyStock": -1,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
