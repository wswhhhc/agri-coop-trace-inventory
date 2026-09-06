from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import Select, asc, desc, false, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models import (
    Batch,
    Inventory,
    InventoryOperation,
    InventoryTransaction,
    InventoryTransactionType,
    Product,
    Warehouse,
)


class InventoryRepository:
    """库存、库存操作头和流水的数据访问仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_inventory(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        warehouse_id: UUID | None,
        product_id: UUID | None,
        batch_id: UUID | None,
        keyword: str | None,
        stock_risk: str | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Inventory], int]:
        conditions = self._scope_conditions(cooperative_id, warehouse_ids)
        if warehouse_id is not None:
            conditions.append(Inventory.warehouse_id == warehouse_id)
        if product_id is not None:
            conditions.append(Batch.product_id == product_id)
        if batch_id is not None:
            conditions.append(Inventory.batch_id == batch_id)
        if keyword:
            pattern = f"%{keyword.strip()}%"
            conditions.append(or_(Product.name.ilike(pattern), Batch.batch_no.ilike(pattern)))
        if stock_risk is not None:
            conditions.append(self._risk_condition(stock_risk))

        statement: Select[tuple[Inventory]] = (
            select(Inventory)
            .join(Inventory.batch)
            .join(Batch.product)
            .options(
                selectinload(Inventory.warehouse),
                selectinload(Inventory.batch).selectinload(Batch.product),
            )
            .where(*conditions)
        )
        count_statement = (
            select(func.count(Inventory.id))
            .join(Inventory.batch)
            .join(Batch.product)
            .where(*conditions)
        )
        total = await self.session.scalar(count_statement)
        sort_column = {
            "quantity": Inventory.quantity,
            "updatedAt": Inventory.updated_at,
            "updated_at": Inventory.updated_at,
            "createdAt": Inventory.updated_at,
        }.get(sort_by, Inventory.updated_at)
        ordering = desc(sort_column) if sort_order == "DESC" else asc(sort_column)
        result = await self.session.scalars(
            statement.order_by(ordering, Inventory.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def get_inventory(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        inventory_id: UUID,
    ) -> Inventory | None:
        statement = (
            select(Inventory)
            .options(
                selectinload(Inventory.warehouse),
                selectinload(Inventory.batch).selectinload(Batch.product),
            )
            .where(Inventory.id == inventory_id)
        )
        for condition in self._scope_conditions(cooperative_id, warehouse_ids):
            statement = statement.where(condition)
        return await self.session.scalar(statement)

    async def list_transactions(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        warehouse_id: UUID | None,
        batch_id: UUID | None,
        transaction_type: InventoryTransactionType | None,
        occurred_at_from: datetime | None,
        occurred_at_to: datetime | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[InventoryTransaction], int]:
        conditions = self._transaction_scope_conditions(cooperative_id, warehouse_ids)
        if warehouse_id is not None:
            conditions.append(InventoryTransaction.warehouse_id == warehouse_id)
        if batch_id is not None:
            conditions.append(InventoryTransaction.batch_id == batch_id)
        if transaction_type is not None:
            conditions.append(InventoryTransaction.transaction_type == transaction_type)
        if occurred_at_from is not None:
            conditions.append(InventoryTransaction.occurred_at >= occurred_at_from)
        if occurred_at_to is not None:
            conditions.append(InventoryTransaction.occurred_at <= occurred_at_to)

        statement: Select[tuple[InventoryTransaction]] = (
            select(InventoryTransaction)
            .options(selectinload(InventoryTransaction.operation))
            .where(*conditions)
        )
        total = await self.session.scalar(
            select(func.count(InventoryTransaction.id)).where(*conditions)
        )
        sort_column = {
            "occurredAt": InventoryTransaction.occurred_at,
            "occurred_at": InventoryTransaction.occurred_at,
            "createdAt": InventoryTransaction.created_at,
            "created_at": InventoryTransaction.created_at,
        }.get(sort_by, InventoryTransaction.occurred_at)
        ordering = desc(sort_column) if sort_order == "DESC" else asc(sort_column)
        result = await self.session.scalars(
            statement.order_by(ordering, InventoryTransaction.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def get_transaction(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        transaction_id: UUID,
    ) -> InventoryTransaction | None:
        statement = (
            select(InventoryTransaction)
            .options(selectinload(InventoryTransaction.operation))
            .where(InventoryTransaction.id == transaction_id)
        )
        for condition in self._transaction_scope_conditions(cooperative_id, warehouse_ids):
            statement = statement.where(condition)
        return await self.session.scalar(statement)

    async def get_warehouse(
        self, cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None, warehouse_id: UUID
    ) -> Warehouse | None:
        statement = select(Warehouse).where(Warehouse.id == warehouse_id)
        for condition in self._warehouse_scope_conditions(cooperative_id, warehouse_ids):
            statement = statement.where(condition)
        return await self.session.scalar(statement)

    async def get_batch(
        self, cooperative_id: UUID | None, batch_id: UUID
    ) -> Batch | None:
        statement = select(Batch).options(selectinload(Batch.product)).where(Batch.id == batch_id)
        if cooperative_id is not None:
            statement = statement.where(Batch.cooperative_id == cooperative_id)
        return await self.session.scalar(statement)

    async def ensure_inventory_row(
        self, cooperative_id: UUID, warehouse_id: UUID, batch_id: UUID
    ) -> Inventory:
        statement = (
            insert(Inventory)
            .values(
                cooperative_id=cooperative_id,
                warehouse_id=warehouse_id,
                batch_id=batch_id,
                quantity=0,
                locked_quantity=0,
                version=0,
            )
            .on_conflict_do_nothing(index_elements=["warehouse_id", "batch_id"])
        )
        await self.session.execute(statement)
        inventory = await self.session.scalar(
            select(Inventory)
            .where(Inventory.warehouse_id == warehouse_id)
            .where(Inventory.batch_id == batch_id)
            .with_for_update()
        )
        if inventory is None:
            raise RuntimeError("库存行创建失败")
        return inventory

    async def lock_inventory(
        self, cooperative_id: UUID, warehouse_id: UUID, batch_id: UUID
    ) -> Inventory | None:
        return await self.session.scalar(
            select(Inventory)
            .where(Inventory.cooperative_id == cooperative_id)
            .where(Inventory.warehouse_id == warehouse_id)
            .where(Inventory.batch_id == batch_id)
            .with_for_update()
        )

    async def add_operation(self, operation: InventoryOperation) -> InventoryOperation:
        self.session.add(operation)
        await self.session.flush()
        return operation

    async def add_transaction(
        self, transaction: InventoryTransaction
    ) -> InventoryTransaction:
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def update_inventory(
        self, inventory: Inventory, *, quantity, version: int
    ) -> Inventory:
        inventory.quantity = quantity
        inventory.version = version
        await self.session.flush()
        return inventory

    @staticmethod
    def _scope_conditions(
        cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(Inventory.cooperative_id == cooperative_id)
        if warehouse_ids is not None:
            conditions.append(
                false() if not warehouse_ids else Inventory.warehouse_id.in_(warehouse_ids)
            )
        return conditions

    @staticmethod
    def _transaction_scope_conditions(
        cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(InventoryTransaction.cooperative_id == cooperative_id)
        if warehouse_ids is not None:
            conditions.append(
                false()
                if not warehouse_ids
                else InventoryTransaction.warehouse_id.in_(warehouse_ids)
            )
        return conditions

    @staticmethod
    def _warehouse_scope_conditions(
        cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(Warehouse.cooperative_id == cooperative_id)
        if warehouse_ids is not None:
            conditions.append(false() if not warehouse_ids else Warehouse.id.in_(warehouse_ids))
        return conditions

    @staticmethod
    def _risk_condition(risk: str) -> ColumnElement[bool]:
        available = Inventory.quantity - Inventory.locked_quantity
        low_stock = available < Product.safety_stock
        near_expiry = Batch.expiry_date <= datetime.now(UTC).date() + timedelta(days=30)
        overstock = (Product.safety_stock > 0) & (Inventory.quantity >= Product.safety_stock * 10)
        if risk == "LOW_STOCK":
            return low_stock
        if risk == "NEAR_EXPIRY":
            return near_expiry
        if risk == "OVERSTOCK":
            return overstock
        return ~or_(low_stock, near_expiry, overstock)


__all__ = ["InventoryRepository"]
