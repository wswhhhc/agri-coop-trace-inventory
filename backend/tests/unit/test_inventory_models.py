from __future__ import annotations

from app.models import (
    Base,
    IdempotencyRecord,
    Inventory,
    InventoryOperation,
    InventoryOperationStatus,
    InventoryOperationType,
    InventoryTransaction,
    InventoryTransactionType,
)
from sqlalchemy import inspect


def test_inventory_models_are_registered_and_split_by_business() -> None:
    assert Inventory.__module__ == "app.models.inventory"
    assert InventoryOperation.__module__ == "app.models.inventory_operation"
    assert InventoryTransaction.__module__ == "app.models.inventory_transaction"
    assert IdempotencyRecord.__module__ == "app.models.idempotency_record"
    assert {
        "inventories",
        "inventory_operations",
        "inventory_transactions",
        "idempotency_records",
    }.issubset(Base.metadata.tables)


def test_inventory_models_match_database_contract() -> None:
    assert {
        "id",
        "cooperative_id",
        "warehouse_id",
        "batch_id",
        "quantity",
        "locked_quantity",
        "version",
        "updated_at",
    } == {column.name for column in inspect(Inventory).columns}
    assert {
        "id",
        "cooperative_id",
        "operation_no",
        "operation_type",
        "source_warehouse_id",
        "destination_warehouse_id",
        "external_reference",
        "reason",
        "occurred_at",
        "status",
        "created_by",
        "created_at",
    } == {column.name for column in inspect(InventoryOperation).columns}
    assert {
        "id",
        "cooperative_id",
        "operation_id",
        "warehouse_id",
        "batch_id",
        "transaction_type",
        "quantity_delta",
        "quantity_before",
        "quantity_after",
        "occurred_at",
        "created_by",
        "created_at",
    } == {column.name for column in inspect(InventoryTransaction).columns}
    assert {
        "id",
        "cooperative_id",
        "user_id",
        "endpoint",
        "idempotency_key",
        "request_hash",
        "status",
        "response_status",
        "response_body",
        "expires_at",
        "created_at",
        "updated_at",
    } == {column.name for column in inspect(IdempotencyRecord).columns}

    assert inspect(InventoryOperation).columns.operation_type.type.enum_class is InventoryOperationType
    assert inspect(InventoryOperation).columns.status.type.enum_class is InventoryOperationStatus
    assert inspect(InventoryTransaction).columns.transaction_type.type.enum_class is InventoryTransactionType
    assert inspect(InventoryOperation).columns.occurred_at.type.timezone is True
    assert inspect(InventoryTransaction).columns.occurred_at.type.timezone is True
    assert inspect(IdempotencyRecord).columns.expires_at.type.timezone is True
    assert {
        constraint.name for constraint in Inventory.__table__.constraints
    } >= {
        "ck_inventories_quantity",
        "ck_inventories_locked_quantity",
        "ck_inventories_version",
        "uq_inventories_warehouse_batch",
    }
    assert {
        constraint.name for constraint in IdempotencyRecord.__table__.constraints
    } >= {"uq_idempotency_records_request"}
