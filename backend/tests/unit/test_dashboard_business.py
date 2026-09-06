from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from app.core.auth.context import AuthContext
from app.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
    Batch,
    BatchStatus,
    Cooperative,
    DataType,
    ForecastResult,
    Inventory,
    InventoryOperation,
    InventoryOperationType,
    InventoryTransaction,
    InventoryTransactionType,
    ModelType,
    ModelVersion,
    Product,
    ProductCategory,
    Role,
    User,
    Warehouse,
)
from app.schemas.dashboard import DashboardQueryParams, ProductRankingParams
from app.services.dashboard import DashboardService

pytestmark = pytest.mark.postgres


@pytest.fixture
def dashboard_context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="dashboard-admin",
        real_name="大屏管理员",
        role_code="COOPERATIVE_ADMIN",
        permission_codes=frozenset({"inventory:read"}),
        cooperative_id=None,
        warehouse_ids=None,
        session_id="dashboard-session",
        token_id="dashboard-token",
    )


@pytest.mark.asyncio
async def test_dashboard_summary_and_inventory_trends_group_units_and_respect_dates(
    postgres_session, dashboard_context: AuthContext
) -> None:
    cooperative = Cooperative(code=f"dashboard-{uuid4().hex[:8]}", name="大屏合作社")
    category = ProductCategory(cooperative=cooperative, code="fresh", name="生鲜")
    product = Product(
        cooperative=cooperative,
        category=category,
        code="tomato",
        name="番茄",
        unit="KG",
        shelf_life_days=30,
        safety_stock=Decimal("90.000"),
    )
    box_product = Product(
        cooperative=cooperative,
        category=category,
        code="box",
        name="礼盒",
        unit="BOX",
        shelf_life_days=30,
        safety_stock=Decimal("5.000"),
    )
    warehouse = Warehouse(cooperative=cooperative, code="WH-1", name="一号仓")
    role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
    user = User(
        cooperative=cooperative,
        role=role,
        username=f"dashboard-{uuid4().hex[:8]}",
        password_hash="unused",
        real_name="大屏管理员",
    )
    batch = Batch(
        cooperative=cooperative,
        product=product,
        creator=user,
        batch_no=f"B-{uuid4().hex[:8]}",
        trace_code=f"T-{uuid4().hex[:8]}",
        origin="测试基地",
        production_date=date(2026, 8, 1),
        expiry_date=date(2026, 9, 15),
        status=BatchStatus.IN_STOCK,
    )
    box_batch = Batch(
        cooperative=cooperative,
        product=box_product,
        creator=user,
        batch_no=f"B-{uuid4().hex[:8]}",
        trace_code=f"T-{uuid4().hex[:8]}",
        origin="测试基地",
        production_date=date(2026, 8, 1),
        expiry_date=date(2027, 1, 1),
        status=BatchStatus.IN_STOCK,
    )
    postgres_session.add_all(
        [cooperative, category, product, box_product, warehouse, role, user, batch, box_batch]
    )
    await postgres_session.flush()

    operation_in = InventoryOperation(
        cooperative_id=cooperative.id,
        operation_no=f"IN-{uuid4().hex[:8]}",
        operation_type=InventoryOperationType.INBOUND,
        occurred_at=datetime(2026, 9, 1, 1, tzinfo=UTC),
        created_by=user.id,
    )
    operation_out = InventoryOperation(
        cooperative_id=cooperative.id,
        operation_no=f"OUT-{uuid4().hex[:8]}",
        operation_type=InventoryOperationType.OUTBOUND,
        occurred_at=datetime(2026, 9, 2, 1, tzinfo=UTC),
        created_by=user.id,
    )
    postgres_session.add_all([operation_in, operation_out])
    await postgres_session.flush()
    postgres_session.add_all(
        [
            Inventory(
                cooperative_id=cooperative.id,
                warehouse_id=warehouse.id,
                batch_id=batch.id,
                quantity=Decimal("80.000"),
                locked_quantity=Decimal("5.000"),
            ),
            Inventory(
                cooperative_id=cooperative.id,
                warehouse_id=warehouse.id,
                batch_id=box_batch.id,
                quantity=Decimal("3.000"),
            ),
            InventoryTransaction(
                cooperative_id=cooperative.id,
                operation_id=operation_in.id,
                warehouse_id=warehouse.id,
                batch_id=batch.id,
                transaction_type=InventoryTransactionType.INBOUND,
                quantity_delta=Decimal("100.000"),
                quantity_before=Decimal("0.000"),
                quantity_after=Decimal("100.000"),
                occurred_at=datetime(2026, 9, 1, 1, tzinfo=UTC),
                created_by=user.id,
            ),
            InventoryTransaction(
                cooperative_id=cooperative.id,
                operation_id=operation_out.id,
                warehouse_id=warehouse.id,
                batch_id=batch.id,
                transaction_type=InventoryTransactionType.OUTBOUND,
                quantity_delta=Decimal("-20.000"),
                quantity_before=Decimal("100.000"),
                quantity_after=Decimal("80.000"),
                occurred_at=datetime(2026, 9, 2, 1, tzinfo=UTC),
                created_by=user.id,
            ),
        ]
    )
    postgres_session.add(
        Alert(
            cooperative_id=cooperative.id,
            alert_type=AlertType.LOW_STOCK,
            severity=AlertSeverity.HIGH,
            status=AlertStatus.PENDING,
            warehouse_id=warehouse.id,
            product_id=product.id,
            dedupe_key=f"low-{uuid4().hex}",
            title="库存偏低",
            message="测试预警",
            evidence={},
            detected_at=datetime(2026, 9, 2, 2, tzinfo=UTC),
        )
    )
    model = ModelVersion(
        cooperative_id=cooperative.id,
        warehouse_id=warehouse.id,
        product_id=product.id,
        model_type=ModelType.XGBOOST,
        version=f"v-{uuid4().hex[:8]}",
        data_type=DataType.SYNTHETIC,
        training_start_date=date(2026, 8, 1),
        training_end_date=date(2026, 8, 31),
        random_seed=42,
        parameters={},
        metrics={"mae": 5.0},
        is_active=True,
        created_by=user.id,
    )
    postgres_session.add(model)
    await postgres_session.flush()
    postgres_session.add(
        ForecastResult(
            cooperative_id=cooperative.id,
            warehouse_id=warehouse.id,
            product_id=product.id,
            model_version_id=model.id,
            horizon_days=7,
            forecast_start_date=date(2026, 9, 1),
            forecast_end_date=date(2026, 9, 7),
            predicted_demand=Decimal("25.000"),
            current_stock=Decimal("80.000"),
            recommended_replenishment=Decimal("0.000"),
            data_type=DataType.SYNTHETIC,
            metrics={"mae": 5.0},
            important_factors=["最近7日出库量"],
            limitation_notice="测试数据",
            generated_at=datetime(2026, 9, 3, 1, tzinfo=UTC),
        )
    )
    await postgres_session.flush()
    await postgres_session.commit()

    context = AuthContext(
        user_id=user.id,
        username=user.username,
        real_name=user.real_name,
        role_code="COOPERATIVE_ADMIN",
        permission_codes=frozenset({"inventory:read", "model:read"}),
        cooperative_id=cooperative.id,
        warehouse_ids=None,
        session_id="dashboard-session",
        token_id="dashboard-token",
    )
    service = DashboardService(postgres_session)
    params = DashboardQueryParams(start_date=date(2026, 9, 1), end_date=date(2026, 9, 2))

    summary = await service.summary(context, params)
    trends = await service.inventory_trends(context, params)
    distribution = await service.alert_distribution(context, params)
    ranking = await service.product_ranking(
        context,
        ProductRankingParams(
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 2)
        ),
    )
    comparisons = await service.forecast_comparison(
        context,
        DashboardQueryParams(
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 7)
        ),
    )

    assert summary.product_count == 2
    assert summary.batch_count == 2
    assert {item.unit: item.quantity for item in summary.inventory_by_unit} == {
        "KG": 80.0,
        "BOX": 3.0,
    }
    assert summary.pending_alert_count == 1
    assert summary.expiring_batch_count == 1
    assert summary.low_stock_product_count == 2
    assert [(item.date, item.unit, item.inbound_quantity, item.outbound_quantity, item.ending_quantity) for item in trends] == [
        (date(2026, 9, 1), "KG", 100.0, 0.0, 100.0),
        (date(2026, 9, 2), "KG", 0.0, 20.0, 80.0),
    ]
    assert distribution.total_count == 1
    assert [(item.alert_type, item.severity, item.count) for item in distribution.items] == [
        ("LOW_STOCK", "HIGH", 1)
    ]
    assert ranking[0].product_name == "番茄"
    assert ranking[0].outbound_quantity == 20.0
    assert ranking[0].outbound_count == 1
    assert comparisons[0].predicted_demand == 25.0
    assert comparisons[0].actual_demand == 20.0
    assert comparisons[0].absolute_error == 5.0
