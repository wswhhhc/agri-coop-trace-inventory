from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, asc, desc, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models import Batch, BatchStatus, SortDirection


class BatchRepository:
    """批次数据访问仓储，所有查询显式附加认证范围。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_scoped(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        batch_id: UUID,
    ) -> Batch | None:
        statement = select(Batch).where(Batch.id == batch_id)
        for condition in self._scope_conditions(cooperative_id, warehouse_ids):
            statement = statement.where(condition)
        return await self.session.scalar(statement)

    async def list_scoped(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        keyword: str | None,
        product_id: UUID | None,
        warehouse_id: UUID | None,
        status: BatchStatus | None,
        production_date_from,
        production_date_to,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: SortDirection,
    ) -> tuple[list[Batch], int]:
        conditions = self._scope_conditions(cooperative_id, warehouse_ids)
        if keyword:
            pattern = f"%{keyword.strip()}%"
            conditions.append(
                or_(Batch.batch_no.ilike(pattern), Batch.trace_code.ilike(pattern))
            )
        if product_id is not None:
            conditions.append(Batch.product_id == product_id)
        # Batch is cooperative-scoped. warehouse_id is validated against the
        # auth context by the service; actual warehouse inventory filtering
        # belongs to the later inventories slice.
        del warehouse_id
        if status is not None:
            conditions.append(Batch.status == status)
        if production_date_from is not None:
            conditions.append(Batch.production_date >= production_date_from)
        if production_date_to is not None:
            conditions.append(Batch.production_date <= production_date_to)
        statement: Select[tuple[Batch]] = select(Batch).where(*conditions)
        total = await self.session.scalar(select(func.count(Batch.id)).where(*conditions))
        sort_column = {
            "batchNo": Batch.batch_no,
            "batch_no": Batch.batch_no,
            "productionDate": Batch.production_date,
            "production_date": Batch.production_date,
            "expiryDate": Batch.expiry_date,
            "expiry_date": Batch.expiry_date,
            "createdAt": Batch.created_at,
            "created_at": Batch.created_at,
        }.get(sort_by, Batch.created_at)
        ordering = (
            desc(sort_column)
            if sort_order is SortDirection.DESC
            else asc(sort_column)
        )
        result = await self.session.scalars(
            statement.order_by(ordering, Batch.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def add(self, batch: Batch) -> Batch:
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def update(self, batch: Batch, values: dict[str, object]) -> Batch:
        for field, value in values.items():
            setattr(batch, field, value)
        await self.session.flush()
        return batch

    @staticmethod
    def _scope_conditions(
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(Batch.cooperative_id == cooperative_id)
        if warehouse_ids is not None and not warehouse_ids:
            conditions.append(false())
        return conditions


__all__ = ["BatchRepository"]
