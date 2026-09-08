import asyncio
from datetime import date
from uuid import uuid4

import pytest
from app.core.auth.context import AuthContext
from app.models import (
    Cooperative,
    DataType,
    ModelType,
    ModelVersion,
    Product,
    ProductCategory,
    Role,
    User,
    Warehouse,
)
from app.schemas.forecasting import ModelActivationCreate
from app.services.forecasting import ForecastingService
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_concurrent_model_activation_requests_are_serialized(
    postgres_session_factory,
) -> None:
    async with postgres_session_factory() as session:
        cooperative = Cooperative(code="COOP-ACTIVATE", name="激活测试合作社")
        category = ProductCategory(
            cooperative=cooperative, code="VEGETABLE", name="蔬菜"
        )
        warehouse = Warehouse(
            cooperative=cooperative, code="WH-ACTIVATE", name="激活测试仓库"
        )
        role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
        user = User(
            cooperative=cooperative,
            role=role,
            username=f"activation-{uuid4().hex[:8]}",
            password_hash="not-used",
            real_name="激活测试用户",
        )
        product = Product(
            cooperative=cooperative,
            category=category,
            code="TOMATO",
            name="番茄",
            unit="KG",
            shelf_life_days=7,
            safety_stock=10,
        )
        session.add_all([cooperative, category, warehouse, role, user, product])
        await session.flush()

        active_version = ModelVersion(
            cooperative_id=cooperative.id,
            warehouse_id=warehouse.id,
            product_id=product.id,
            model_type=ModelType.XGBOOST,
            version="xgb-active",
            data_type=DataType.SYNTHETIC,
            training_start_date=date(2026, 1, 1),
            training_end_date=date(2026, 1, 31),
            random_seed=42,
            created_by=user.id,
            is_active=True,
        )
        target_version = ModelVersion(
            cooperative_id=cooperative.id,
            warehouse_id=warehouse.id,
            product_id=product.id,
            model_type=ModelType.XGBOOST,
            version="xgb-target",
            data_type=DataType.SYNTHETIC,
            training_start_date=date(2026, 2, 1),
            training_end_date=date(2026, 2, 28),
            random_seed=43,
            created_by=user.id,
            is_active=False,
        )
        second_target_version = ModelVersion(
            cooperative_id=cooperative.id,
            warehouse_id=warehouse.id,
            product_id=product.id,
            model_type=ModelType.XGBOOST,
            version="xgb-second-target",
            data_type=DataType.SYNTHETIC,
            training_start_date=date(2026, 3, 1),
            training_end_date=date(2026, 3, 31),
            random_seed=44,
            created_by=user.id,
            is_active=False,
        )
        session.add_all([active_version, target_version, second_target_version])
        await session.commit()

        context = AuthContext(
            user_id=user.id,
            username=user.username,
            real_name=user.real_name,
            role_code="COOPERATIVE_ADMIN",
            permission_codes=frozenset({"model:manage"}),
            cooperative_id=cooperative.id,
            warehouse_ids=None,
            session_id="session-1",
            token_id="token-1",
        )

    async def activate(version_id) -> bool:
        async with postgres_session_factory() as activation_session:
            try:
                await ForecastingService(activation_session).activate_model(
                    context, ModelActivationCreate(model_version_id=version_id)
                )
            except IntegrityError:
                return False
            return True

    results = await asyncio.gather(
        activate(target_version.id), activate(second_target_version.id)
    )
    assert results == [True, True]

    async with postgres_session_factory() as session:
        versions = list(
            await session.scalars(
                select(ModelVersion).order_by(ModelVersion.version)
            )
        )
        assert sum(version.is_active for version in versions) == 1
