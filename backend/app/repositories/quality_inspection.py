from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models import QualityInspection, SortDirection


class QualityInspectionRepository:
    """质检记录数据访问，查询必须显式带合作社和批次范围。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _options():
        return (
            selectinload(QualityInspection.items),
            selectinload(QualityInspection.inspector),
            selectinload(QualityInspection.file_links),
        )

    async def get_scoped(
        self,
        cooperative_id: UUID | None,
        batch_id: UUID,
        inspection_id: UUID,
    ) -> QualityInspection | None:
        conditions = self._scope_conditions(cooperative_id, batch_id)
        statement = (
            select(QualityInspection)
            .options(*self._options())
            .where(QualityInspection.id == inspection_id, *conditions)
        )
        return await self.session.scalar(statement)

    async def list_scoped(
        self,
        cooperative_id: UUID | None,
        batch_id: UUID,
        *,
        conclusion,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: SortDirection,
    ) -> tuple[list[QualityInspection], int]:
        conditions = self._scope_conditions(cooperative_id, batch_id)
        if conclusion is not None:
            conditions.append(QualityInspection.conclusion == conclusion)
        statement: Select[tuple[QualityInspection]] = (
            select(QualityInspection).options(*self._options()).where(*conditions)
        )
        total = await self.session.scalar(
            select(func.count(QualityInspection.id)).where(*conditions)
        )
        sort_column = {
            "inspectionDate": QualityInspection.inspected_at,
            "inspectedAt": QualityInspection.inspected_at,
            "inspected_at": QualityInspection.inspected_at,
            "createdAt": QualityInspection.created_at,
            "created_at": QualityInspection.created_at,
        }.get(sort_by, QualityInspection.inspected_at)
        ordering = (
            desc(sort_column) if sort_order is SortDirection.DESC else asc(sort_column)
        )
        result = await self.session.scalars(
            statement.order_by(ordering, QualityInspection.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def add(self, inspection: QualityInspection) -> QualityInspection:
        self.session.add(inspection)
        await self.session.flush()
        return inspection

    @staticmethod
    def _scope_conditions(
        cooperative_id: UUID | None,
        batch_id: UUID,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [
            QualityInspection.batch_id == batch_id
        ]
        if cooperative_id is not None:
            conditions.append(QualityInspection.cooperative_id == cooperative_id)
        return conditions


__all__ = ["QualityInspectionRepository"]
