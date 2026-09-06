from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from app.core.auth.context import AuthContext
from app.core.config import Settings
from app.core.exceptions import AppException
from app.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
    Batch,
    BatchStatus,
    Cooperative,
    Inventory,
    InventoryOperation,
    InventoryOperationType,
    InventoryTransaction,
    InventoryTransactionType,
    Product,
    ProductCategory,
    Role,
    TaskRecord,
    TaskStatus,
    User,
    Warehouse,
)
from app.schemas.export import ExportTaskCreate
from app.services.export import ExportService
from app.services.task import TaskService

pytestmark = pytest.mark.postgres


def _context(user_id, cooperative_id, permissions: set[str]) -> AuthContext:
    return AuthContext(
        user_id=user_id,
        username="export-admin",
        real_name="导出管理员",
        role_code="COOPERATIVE_ADMIN",
        permission_codes=frozenset(permissions),
        cooperative_id=cooperative_id,
        warehouse_ids=None,
        session_id="export-session",
        token_id="export-token",
    )


@pytest.mark.asyncio
async def test_export_repository_returns_scoped_inventory_and_alert_rows(postgres_session) -> None:
    cooperative = Cooperative(code=f"export-{uuid4().hex[:8]}", name="导出合作社")
    category = ProductCategory(cooperative=cooperative, code="fresh", name="生鲜")
    product = Product(
        cooperative=cooperative,
        category=category,
        code="tomato",
        name="番茄",
        unit="KG",
        shelf_life_days=10,
        safety_stock=Decimal(5),
    )
    warehouse = Warehouse(cooperative=cooperative, code="WH-1", name="一号仓")
    role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
    user = User(
        cooperative=cooperative,
        role=role,
        username=f"export-{uuid4().hex[:8]}",
        password_hash="unused",
        real_name="导出管理员",
    )
    batch = Batch(
        cooperative=cooperative,
        product=product,
        creator=user,
        batch_no=f"B-{uuid4().hex[:8]}",
        trace_code=f"T-{uuid4().hex[:8]}",
        origin="测试基地",
        production_date=date(2026, 9, 1),
        expiry_date=date(2026, 9, 10),
        status=BatchStatus.IN_STOCK,
    )
    postgres_session.add_all([cooperative, category, product, warehouse, role, user, batch])
    await postgres_session.flush()
    operation = InventoryOperation(
        cooperative_id=cooperative.id,
        operation_no=f"IN-{uuid4().hex[:8]}",
        operation_type=InventoryOperationType.INBOUND,
        occurred_at=datetime(2026, 9, 3, tzinfo=UTC),
        created_by=user.id,
    )
    postgres_session.add(operation)
    await postgres_session.flush()
    postgres_session.add_all(
        [
            Inventory(
                cooperative_id=cooperative.id,
                warehouse_id=warehouse.id,
                batch_id=batch.id,
                quantity=Decimal(12),
                locked_quantity=Decimal(2),
            ),
            InventoryTransaction(
                cooperative_id=cooperative.id,
                operation_id=operation.id,
                warehouse_id=warehouse.id,
                batch_id=batch.id,
                transaction_type=InventoryTransactionType.INBOUND,
                quantity_delta=Decimal(12),
                quantity_before=Decimal(0),
                quantity_after=Decimal(12),
                occurred_at=datetime(2026, 9, 3, tzinfo=UTC),
                created_by=user.id,
            ),
            Alert(
                cooperative_id=cooperative.id,
                alert_type=AlertType.LOW_STOCK,
                severity=AlertSeverity.HIGH,
                status=AlertStatus.PENDING,
                warehouse_id=warehouse.id,
                product_id=product.id,
                batch_id=batch.id,
                dedupe_key=f"export-{uuid4().hex}",
                title="库存不足",
                message="测试预警",
                evidence={"quantity": 2},
                detected_at=datetime(2026, 9, 4, tzinfo=UTC),
            ),
        ]
    )
    await postgres_session.commit()

    service = ExportService(postgres_session)
    inventory_rows = await service.repository.list_inventory_rows(
        cooperative.id,
        warehouse.id,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 3),
    )
    alert_rows = await service.repository.list_alert_rows(
        cooperative.id,
        warehouse.id,
        start_date=date(2026, 9, 4),
        end_date=date(2026, 9, 4),
    )

    assert inventory_rows[0]["product_name"] == "番茄"
    assert inventory_rows[0]["available_quantity"] == Decimal("10.000")
    assert alert_rows[0]["alert_type"] == "LOW_STOCK"
    assert alert_rows[0]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_export_service_creates_task_with_scoped_payload_and_enqueues(postgres_session) -> None:
    cooperative = Cooperative(code=f"export-{uuid4().hex[:8]}", name="导出合作社")
    warehouse = Warehouse(cooperative=cooperative, code="WH-1", name="一号仓")
    role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
    user = User(
        cooperative=cooperative,
        role=role,
        username=f"export-{uuid4().hex[:8]}",
        password_hash="unused",
        real_name="导出管理员",
    )
    postgres_session.add_all([cooperative, warehouse, role, user])
    await postgres_session.commit()

    enqueued: dict[str, object] = {}

    def enqueue(*, args, kwargs, task_id):
        enqueued.update(args=args, kwargs=kwargs, task_id=task_id)

    task = await ExportService(postgres_session).submit(
        _context(user.id, cooperative.id, {"inventory:read"}),
        ExportTaskCreate(
            reportType="INVENTORY_DETAIL",
            filters={
                "warehouseId": str(warehouse.id),
                "startDate": "2026-09-01",
                "endDate": "2026-09-03",
            },
        ),
        enqueue,
    )

    assert task.task_type == "EXPORT_REPORT"
    assert task.request_payload["reportType"] == "INVENTORY_DETAIL"
    assert task.request_payload["filters"]["warehouseId"] == str(warehouse.id)
    assert enqueued["args"] == [str(task.id)]
    assert enqueued["task_id"] == task.celery_task_id

    readable_task = await TaskService(postgres_session).get(
        _context(user.id, cooperative.id, {"inventory:read"}), task.id
    )
    assert readable_task.id == task.id


@pytest.mark.asyncio
async def test_export_download_checks_expiration_and_returns_only_safe_file(
    postgres_session, tmp_path
) -> None:
    cooperative = Cooperative(code=f"export-{uuid4().hex[:8]}", name="导出合作社")
    role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
    user = User(
        cooperative=cooperative,
        role=role,
        username=f"export-{uuid4().hex[:8]}",
        password_hash="unused",
        real_name="导出管理员",
    )
    postgres_session.add_all([cooperative, role, user])
    await postgres_session.flush()
    task = TaskRecord(
        cooperative_id=cooperative.id,
        task_type="EXPORT_REPORT",
        celery_task_id=str(uuid4()),
        status=TaskStatus.SUCCESS,
        requested_by=user.id,
        request_payload={"reportType": "INVENTORY_DETAIL", "filters": {}},
        result_payload={
            "downloadUrl": f"/api/v1/export-files/{uuid4()}",
            "expiresAt": "2099-01-01T00:00:00+00:00",
            "filename": "inventory_detail_safe.xlsx",
        },
    )
    postgres_session.add(task)
    await postgres_session.commit()
    (tmp_path / "inventory_detail_safe.xlsx").write_bytes(b"xlsx")
    settings = Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
        export_storage_dir=str(tmp_path),
    )
    context = _context(user.id, cooperative.id, {"inventory:read"})
    path, filename = await ExportService(postgres_session).download(
        context, task.id, settings
    )

    assert path == (tmp_path / "inventory_detail_safe.xlsx").resolve()
    assert filename == "inventory_detail_safe.xlsx"

    task.result_payload = {
        **task.result_payload,
        "expiresAt": "2020-01-01T00:00:00+00:00",
    }
    await postgres_session.commit()
    with pytest.raises(AppException) as error:
        await ExportService(postgres_session).download(context, task.id, settings)
    assert error.value.code == "EXPORT_EXPIRED"
