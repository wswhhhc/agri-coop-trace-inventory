from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import asc, desc, false, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models import (
    Batch,
    ForecastResult,
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
    ModelVersion,
    Product,
    TaskRecord,
    Warehouse,
)


class ForecastingRepository:
    """模型版本、预测结果和异步任务的数据访问。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_task(self, record: TaskRecord) -> TaskRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def add_model_version(self, version: ModelVersion) -> ModelVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def add_forecast_result(self, result: ForecastResult) -> ForecastResult:
        self.session.add(result)
        await self.session.flush()
        return result

    async def list_outbound_transactions(
        self,
        cooperative_id: UUID,
        warehouse_id: UUID,
        product_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[InventoryTransaction]:
        result = await self.session.scalars(
            select(InventoryTransaction)
            .join(Batch, Batch.id == InventoryTransaction.batch_id)
            .where(
                InventoryTransaction.cooperative_id == cooperative_id,
                InventoryTransaction.warehouse_id == warehouse_id,
                Batch.product_id == product_id,
                InventoryTransaction.transaction_type
                == InventoryTransactionType.OUTBOUND,
                InventoryTransaction.occurred_at >= start_date,
                InventoryTransaction.occurred_at < end_date,
            )
            .order_by(InventoryTransaction.occurred_at)
        )
        return list(result)

    async def current_stock(
        self, cooperative_id: UUID, warehouse_id: UUID, product_id: UUID
    ) -> Decimal:
        value = await self.session.scalar(
            select(func.coalesce(func.sum(Inventory.quantity), 0))
            .join(Batch, Batch.id == Inventory.batch_id)
            .where(
                Inventory.cooperative_id == cooperative_id,
                Inventory.warehouse_id == warehouse_id,
                Batch.product_id == product_id,
            )
        )
        return value or Decimal(0)

    async def get_warehouse(
        self, cooperative_id: UUID, warehouse_id: UUID
    ) -> Warehouse | None:
        return await self.session.scalar(
            select(Warehouse).where(
                Warehouse.id == warehouse_id, Warehouse.cooperative_id == cooperative_id
            )
        )

    async def get_product(
        self, cooperative_id: UUID, product_id: UUID
    ) -> Product | None:
        return await self.session.scalar(
            select(Product).where(
                Product.id == product_id, Product.cooperative_id == cooperative_id
            )
        )

    async def lock_model_activation_scope(
        self, cooperative_id: UUID, warehouse_id: UUID, product_id: UUID
    ) -> None:
        """串行化同一合作社、仓库和产品范围内的模型激活。"""
        scope_key = f"{cooperative_id}:{warehouse_id}:{product_id}"
        await self.session.execute(
            select(
                func.pg_advisory_xact_lock(
                    func.hashtextextended(scope_key, 0)
                )
            )
        )

    async def list_model_versions(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        warehouse_id: UUID | None,
        product_id: UUID | None,
        is_active: bool | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[ModelVersion], int]:
        conditions = self._scope(ModelVersion, cooperative_id, warehouse_ids)
        if warehouse_id is not None:
            conditions.append(ModelVersion.warehouse_id == warehouse_id)
        if product_id is not None:
            conditions.append(ModelVersion.product_id == product_id)
        if is_active is not None:
            conditions.append(ModelVersion.is_active.is_(is_active))
        total = await self.session.scalar(
            select(func.count(ModelVersion.id)).where(*conditions)
        )
        sort_column = (
            ModelVersion.created_at
            if sort_by not in {"version", "trainingStartDate"}
            else getattr(
                ModelVersion,
                "version" if sort_by == "version" else "training_start_date",
            )
        )
        ordering = desc(sort_column) if sort_order == "DESC" else asc(sort_column)
        result = await self.session.scalars(
            select(ModelVersion)
            .where(*conditions)
            .order_by(ordering, ModelVersion.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def get_model_version(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        model_version_id: UUID,
        *,
        lock: bool = False,
    ) -> ModelVersion | None:
        statement = select(ModelVersion).where(
            ModelVersion.id == model_version_id,
            *self._scope(ModelVersion, cooperative_id, warehouse_ids),
        )
        if lock:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def deactivate_scope(
        self, cooperative_id: UUID, warehouse_id: UUID, product_id: UUID
    ) -> None:
        versions = await self.session.scalars(
            select(ModelVersion)
            .where(
                ModelVersion.cooperative_id == cooperative_id,
                ModelVersion.warehouse_id == warehouse_id,
                ModelVersion.product_id == product_id,
                ModelVersion.is_active.is_(True),
            )
            .with_for_update()
        )
        for version in versions:
            version.is_active = False

    async def get_active_model(
        self, cooperative_id: UUID, warehouse_id: UUID, product_id: UUID
    ) -> ModelVersion | None:
        return await self.session.scalar(
            select(ModelVersion)
            .where(
                ModelVersion.cooperative_id == cooperative_id,
                ModelVersion.warehouse_id == warehouse_id,
                ModelVersion.product_id == product_id,
                ModelVersion.is_active.is_(True),
            )
            .order_by(ModelVersion.created_at.desc())
        )

    async def list_forecast_results(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        warehouse_id: UUID | None,
        product_id: UUID | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[ForecastResult], int]:
        conditions = self._scope(ForecastResult, cooperative_id, warehouse_ids)
        if warehouse_id is not None:
            conditions.append(ForecastResult.warehouse_id == warehouse_id)
        if product_id is not None:
            conditions.append(ForecastResult.product_id == product_id)
        total = await self.session.scalar(
            select(func.count(ForecastResult.id)).where(*conditions)
        )
        sort_column = ForecastResult.generated_at
        ordering = desc(sort_column) if sort_order == "DESC" else asc(sort_column)
        result = await self.session.scalars(
            select(ForecastResult)
            .options(selectinload(ForecastResult.points))
            .where(*conditions)
            .order_by(ordering, ForecastResult.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def get_forecast_result(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        result_id: UUID,
    ) -> ForecastResult | None:
        return await self.session.scalar(
            select(ForecastResult)
            .options(selectinload(ForecastResult.points))
            .where(
                ForecastResult.id == result_id,
                *self._scope(ForecastResult, cooperative_id, warehouse_ids),
            )
        )

    @staticmethod
    def _scope(
        model, cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(model.cooperative_id == cooperative_id)
        if warehouse_ids is not None:
            conditions.append(
                false() if not warehouse_ids else model.warehouse_id.in_(warehouse_ids)
            )
        return conditions


__all__ = ["ForecastingRepository"]
