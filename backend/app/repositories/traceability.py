from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models import (
    Batch,
    Product,
    QualityInspection,
    SortDirection,
    TraceEvent,
    TraceEventType,
)


class TraceEventRepository:
    """追溯事件数据访问；事件只允许追加，查询显式附加合作社范围。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, event: TraceEvent) -> TraceEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_scoped(
        self,
        cooperative_id: UUID | None,
        batch_id: UUID,
        *,
        event_type: TraceEventType | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: SortDirection,
    ) -> tuple[list[TraceEvent], int]:
        conditions = self._scope_conditions(cooperative_id, batch_id)
        if event_type is not None:
            conditions.append(TraceEvent.event_type == event_type)
        statement: Select[tuple[TraceEvent]] = select(TraceEvent).where(*conditions)
        total = await self.session.scalar(select(func.count(TraceEvent.id)).where(*conditions))
        sort_column = {
            "eventTime": TraceEvent.event_time,
            "event_time": TraceEvent.event_time,
            "createdAt": TraceEvent.created_at,
            "created_at": TraceEvent.created_at,
        }.get(sort_by, TraceEvent.event_time)
        ordering = (
            desc(sort_column)
            if sort_order is SortDirection.DESC
            else asc(sort_column)
        )
        result = await self.session.scalars(
            statement.order_by(ordering, TraceEvent.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    @staticmethod
    def _scope_conditions(
        cooperative_id: UUID | None,
        batch_id: UUID,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [TraceEvent.batch_id == batch_id]
        if cooperative_id is not None:
            conditions.append(TraceEvent.cooperative_id == cooperative_id)
        return conditions

    async def get_public_batch(self, trace_code: str) -> Batch | None:
        """按全局唯一追溯码一次加载公开投影所需的关联数据。"""
        statement = (
            select(Batch)
            .options(
                selectinload(Batch.product).selectinload(Product.category),
                selectinload(Batch.quality_inspections).selectinload(
                    QualityInspection.items
                ),
                selectinload(Batch.trace_events),
            )
            .where(Batch.trace_code == trace_code)
        )
        return await self.session.scalar(statement)


__all__ = ["TraceEventRepository"]
