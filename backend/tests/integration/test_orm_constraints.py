from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from app.models import Batch, Cooperative, Product
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import (
    batch_factory,
    cooperative_factory,
    product_category_factory,
    product_factory,
    role_factory,
    user_factory,
    user_warehouse_factory,
    warehouse_factory,
)

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_orm_entities_support_real_create_read_update_delete(
    postgres_session: AsyncSession,
) -> None:
    cooperative = cooperative_factory()
    role = role_factory()
    user = user_factory(cooperative=cooperative, role=role)
    warehouse = warehouse_factory(cooperative=cooperative)
    category = product_category_factory(cooperative=cooperative)
    product = product_factory(cooperative=cooperative, category=category)
    batch = batch_factory(
        cooperative=cooperative,
        product=product,
        creator=user,
    )
    user_warehouse = user_warehouse_factory(user=user, warehouse=warehouse)

    postgres_session.add_all(
        [role, user, warehouse, category, product, batch, user_warehouse]
    )
    await postgres_session.commit()

    loaded = await postgres_session.scalar(
        select(Product).where(Product.id == product.id)
    )
    assert loaded is not None
    assert loaded.code == product.code

    loaded.name = "更新后的测试农产品"
    await postgres_session.commit()
    await postgres_session.refresh(loaded)
    assert loaded.name == "更新后的测试农产品"

    await postgres_session.delete(batch)
    await postgres_session.commit()
    assert await postgres_session.get(Batch, batch.id) is None


@pytest.mark.asyncio
async def test_unique_cooperative_code_is_enforced_by_postgresql(
    postgres_session: AsyncSession,
) -> None:
    postgres_session.add(cooperative_factory(code="same-code"))
    await postgres_session.commit()

    postgres_session.add(cooperative_factory(code="same-code"))
    with pytest.raises(IntegrityError):
        await postgres_session.commit()
    await postgres_session.rollback()


@pytest.mark.asyncio
async def test_concurrent_unique_cooperative_inserts_allow_only_one_commit(
    postgres_session_factory,
) -> None:
    async def create_cooperative() -> bool:
        async with postgres_session_factory() as session:
            session.add(cooperative_factory(code="concurrent-code"))
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                return False
            return True

    results = await asyncio.gather(create_cooperative(), create_cooperative())

    assert sorted(results) == [False, True]
    async with postgres_session_factory() as session:
        count = await session.scalar(
            select(Cooperative.id).where(Cooperative.code == "concurrent-code")
        )
    assert count is not None


@pytest.mark.asyncio
async def test_composite_product_code_is_unique_per_cooperative(
    postgres_session: AsyncSession,
) -> None:
    cooperative = cooperative_factory()
    category = product_category_factory(cooperative=cooperative)
    postgres_session.add(product_factory(cooperative=cooperative, category=category, code="tomato"))
    await postgres_session.commit()

    postgres_session.add(product_factory(cooperative=cooperative, category=category, code="tomato"))
    with pytest.raises(IntegrityError):
        await postgres_session.commit()
    await postgres_session.rollback()


@pytest.mark.asyncio
async def test_foreign_key_rejects_product_with_unknown_parent_ids(
    postgres_session: AsyncSession,
) -> None:
    postgres_session.add(
        Product(
            cooperative_id=uuid4(),
            category_id=uuid4(),
            code="orphan-product",
            name="孤立产品",
            unit="kg",
            shelf_life_days=7,
            safety_stock=Decimal("1.000"),
        )
    )
    with pytest.raises(IntegrityError):
        await postgres_session.commit()
    await postgres_session.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"),
    [("shelf_life_days", 0), ("safety_stock", Decimal("-0.001"))],
)
async def test_product_numeric_checks_reject_invalid_values(
    postgres_session: AsyncSession,
    field: str,
    value: int | Decimal,
) -> None:
    product = product_factory(**{field: value})
    postgres_session.add(product)
    with pytest.raises(IntegrityError):
        await postgres_session.commit()
    await postgres_session.rollback()


@pytest.mark.asyncio
async def test_batch_date_check_rejects_expiry_before_production(
    postgres_session: AsyncSession,
) -> None:
    product = product_factory()
    user = user_factory(cooperative=product.cooperative)
    postgres_session.add(
        batch_factory(
            cooperative=product.cooperative,
            product=product,
            creator=user,
            production_date=date(2026, 9, 5),
            expiry_date=date(2026, 9, 4),
        )
    )
    with pytest.raises(IntegrityError):
        await postgres_session.commit()
    await postgres_session.rollback()


@pytest.mark.asyncio
async def test_batch_status_check_rejects_value_outside_enum(
    postgres_session: AsyncSession,
) -> None:
    batch = batch_factory()
    postgres_session.add(batch)
    await postgres_session.commit()

    with pytest.raises(IntegrityError):
        await postgres_session.execute(
            text("UPDATE batches SET status = 'INVALID' WHERE id = CAST(:id AS uuid)"),
            {"id": str(batch.id)},
        )
    await postgres_session.rollback()
