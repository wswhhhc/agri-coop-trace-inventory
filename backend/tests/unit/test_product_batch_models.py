from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from app.models import (
    Base,
    Batch,
    BatchStatus,
    Cooperative,
    Product,
    ProductCategory,
    Role,
    User,
)
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def catalog_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


def test_product_and_batch_models_are_registered_in_separate_modules() -> None:
    assert Product.__module__ == "app.models.product"
    assert ProductCategory.__module__ == "app.models.product_category"
    assert Batch.__module__ == "app.models.batch"
    assert {"product_categories", "products", "batches"}.issubset(Base.metadata.tables)
    assert inspect(Product).relationships["category"].mapper.class_ is ProductCategory
    assert inspect(Product).relationships["batches"].mapper.class_ is Batch
    assert inspect(Batch).relationships["product"].mapper.class_ is Product
    assert inspect(Batch).relationships["creator"].mapper.class_ is User


def test_product_and_batch_have_the_expected_columns_and_constraints() -> None:
    assert {
        "id",
        "cooperative_id",
        "category_id",
        "code",
        "name",
        "unit",
        "shelf_life_days",
        "safety_stock",
        "is_active",
        "created_at",
        "updated_at",
    } == {column.name for column in inspect(Product).columns}
    assert {
        "id",
        "cooperative_id",
        "product_id",
        "batch_no",
        "trace_code",
        "origin",
        "production_date",
        "expiry_date",
        "responsible_person",
        "status",
        "created_by",
        "created_at",
        "updated_at",
    } == {column.name for column in inspect(Batch).columns}
    assert inspect(Batch).columns.status.type.enum_class is BatchStatus
    assert {constraint.name for constraint in Product.__table__.constraints} >= {
        "ck_products_shelf_life",
        "ck_products_safety_stock",
        "uq_products_cooperative_code",
    }
    assert {constraint.name for constraint in Batch.__table__.constraints} >= {
        "ck_batches_date_order",
        "ck_batches_status",
        "uq_batches_batch_no",
        "uq_batches_trace_code",
    }


@pytest.mark.asyncio
async def test_product_and_batch_can_be_created_and_queried_by_orm(
    catalog_session: AsyncSession,
) -> None:
    cooperative = Cooperative(code="coop-1", name="示例合作社")
    role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
    user = User(
        cooperative=cooperative,
        role=role,
        username="catalog_admin",
        password_hash="hashed",
        real_name="目录管理员",
    )
    category = ProductCategory(
        cooperative=cooperative,
        code="vegetable",
        name="蔬菜",
    )
    product = Product(
        cooperative=cooperative,
        category=category,
        code="tomato",
        name="番茄",
        unit="kg",
        shelf_life_days=7,
        safety_stock=Decimal("10.000"),
    )
    batch = Batch(
        cooperative=cooperative,
        product=product,
        batch_no="batch-20260905-01",
        trace_code="trace-20260905-01",
        origin="示例基地",
        production_date=date(2026, 9, 5),
        expiry_date=date(2026, 9, 12),
        creator=user,
        status=BatchStatus.CREATED,
    )

    catalog_session.add(batch)
    await catalog_session.commit()

    loaded = await catalog_session.scalar(
        select(Batch).where(Batch.trace_code == "trace-20260905-01")
    )

    assert loaded is not None
    assert loaded.product_id == product.id
    assert loaded.status is BatchStatus.CREATED
