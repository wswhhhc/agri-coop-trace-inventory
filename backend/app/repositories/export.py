from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Alert,
    Batch,
    Inventory,
    InventoryTransaction,
    Product,
    Warehouse,
)


class ExportRepository:
    """报表导出所需的只读聚合查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def warehouse_in_cooperative(
        self, cooperative_id: UUID, warehouse_id: UUID
    ) -> bool:
        return bool(
            await self.session.scalar(
                select(Warehouse.id).where(
                    Warehouse.id == warehouse_id,
                    Warehouse.cooperative_id == cooperative_id,
                )
            )
        )

    async def list_inventory_rows(
        self,
        cooperative_id: UUID,
        warehouse_id: UUID | None,
        *,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        start_at, end_at = _date_bounds(start_date, end_date)
        statement = (
            select(
                func.max(InventoryTransaction.occurred_at).label("date"),
                Warehouse.name.label("warehouse"),
                Batch.batch_no.label("batch_no"),
                Product.code.label("product_code"),
                Product.name.label("product_name"),
                Product.unit.label("unit"),
                Inventory.quantity.label("quantity"),
                Inventory.locked_quantity.label("locked_quantity"),
                (Inventory.quantity - Inventory.locked_quantity).label(
                    "available_quantity"
                ),
            )
            .select_from(Inventory)
            .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
            .join(Batch, Batch.id == Inventory.batch_id)
            .join(Product, Product.id == Batch.product_id)
            .join(
                InventoryTransaction,
                (InventoryTransaction.warehouse_id == Inventory.warehouse_id)
                & (InventoryTransaction.batch_id == Inventory.batch_id),
            )
            .where(
                Inventory.cooperative_id == cooperative_id,
                InventoryTransaction.cooperative_id == cooperative_id,
                InventoryTransaction.occurred_at >= start_at,
                InventoryTransaction.occurred_at < end_at,
            )
            .group_by(
                Warehouse.name,
                Batch.batch_no,
                Product.code,
                Product.name,
                Product.unit,
                Inventory.quantity,
                Inventory.locked_quantity,
            )
            .order_by(Warehouse.name, Product.name, Batch.batch_no)
        )
        if warehouse_id is not None:
            statement = statement.where(Inventory.warehouse_id == warehouse_id)
        return [dict(row) for row in (await self.session.execute(statement)).mappings().all()]

    async def list_alert_rows(
        self,
        cooperative_id: UUID,
        warehouse_id: UUID | None,
        *,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        start_at, end_at = _date_bounds(start_date, end_date)
        statement = (
            select(
                Alert.detected_at.label("detected_at"),
                Alert.alert_type.label("alert_type"),
                Alert.severity.label("severity"),
                Alert.status.label("status"),
                Warehouse.name.label("warehouse"),
                Product.name.label("product"),
                Batch.batch_no.label("batch_no"),
                Alert.title.label("title"),
                Alert.message.label("message"),
                Alert.resolved_at.label("resolved_at"),
            )
            .select_from(Alert)
            .outerjoin(Warehouse, Warehouse.id == Alert.warehouse_id)
            .outerjoin(Product, Product.id == Alert.product_id)
            .outerjoin(Batch, Batch.id == Alert.batch_id)
            .where(
                Alert.cooperative_id == cooperative_id,
                Alert.detected_at >= start_at,
                Alert.detected_at < end_at,
            )
            .order_by(Alert.detected_at, Alert.id)
        )
        if warehouse_id is not None:
            statement = statement.where(Alert.warehouse_id == warehouse_id)
        return [dict(row) for row in (await self.session.execute(statement)).mappings().all()]


def _date_bounds(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(start_date, datetime.min.time(), tzinfo=UTC),
        datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC),
    )


__all__ = ["ExportRepository"]
