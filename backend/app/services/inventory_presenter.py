from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

from app.models import Inventory, InventoryRisk, InventoryTransaction
from app.schemas.inventory import (
    BatchRef,
    InventoryData,
    InventoryTransactionData,
    ProductRef,
    WarehouseRef,
)


def transaction_data(
    transaction: InventoryTransaction, operation_no: str | None = None
) -> InventoryTransactionData:
    resolved_operation_no = operation_no
    if resolved_operation_no is None:
        resolved_operation_no = transaction.operation.operation_no
    return InventoryTransactionData(
        id=transaction.id,
        transaction_id=transaction.id,
        transaction_no=f"TX-{transaction.id.hex[:20]}",
        operation_id=transaction.operation_id,
        operation_no=resolved_operation_no,
        transaction_type=transaction.transaction_type,
        quantity=float(abs(transaction.quantity_delta)),
        quantity_delta=float(transaction.quantity_delta),
        quantity_before=float(transaction.quantity_before),
        quantity_after=float(transaction.quantity_after),
        warehouse_id=transaction.warehouse_id,
        batch_id=transaction.batch_id,
        occurred_at=transaction.occurred_at,
        created_at=transaction.created_at,
    )


def inventory_data(inventory: Inventory) -> InventoryData:
    risk_flags: list[InventoryRisk] = []
    available = inventory.quantity - inventory.locked_quantity
    if available < inventory.batch.product.safety_stock:
        risk_flags.append(InventoryRisk.LOW_STOCK)
    if inventory.batch.expiry_date <= datetime.now(UTC).date() + timedelta(days=30):
        risk_flags.append(InventoryRisk.NEAR_EXPIRY)
    if (
        inventory.batch.product.safety_stock > 0
        and inventory.quantity >= inventory.batch.product.safety_stock * 10
    ):
        risk_flags.append(InventoryRisk.OVERSTOCK)
    return InventoryData(
        id=inventory.id,
        warehouse=WarehouseRef(id=inventory.warehouse.id, name=inventory.warehouse.name),
        product=ProductRef(
            id=inventory.batch.product.id,
            name=inventory.batch.product.name,
            unit=inventory.batch.product.unit,
        ),
        batch=BatchRef(
            id=inventory.batch.id,
            batch_no=inventory.batch.batch_no,
            expiry_date=inventory.batch.expiry_date,
        ),
        quantity=float(inventory.quantity),
        available_quantity=float(available),
        risk_flags=risk_flags,
        updated_at=inventory.updated_at,
    )


def transaction_dict(
    transaction: InventoryTransaction, operation_no: str
) -> dict[str, object]:
    return cast(
        dict[str, object],
        transaction_data(transaction, operation_no).model_dump(
            mode="json", by_alias=True
        ),
    )


__all__ = ["inventory_data", "transaction_data", "transaction_dict"]
