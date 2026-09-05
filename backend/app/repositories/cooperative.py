from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models import Cooperative, CooperativeStatus, SortDirection


class CooperativeRepository:
    """合作社数据访问仓储，所有业务查询显式接收范围。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, cooperative_id: UUID) -> Cooperative | None:
        return await self.session.get(Cooperative, cooperative_id)

    async def get_by_code(self, code: str) -> Cooperative | None:
        statement = select(Cooperative).where(Cooperative.code == code)
        return await self.session.scalar(statement)

    async def get_scoped(
        self,
        cooperative_id: UUID | None,
        target_id: UUID,
    ) -> Cooperative | None:
        statement = select(Cooperative).where(Cooperative.id == target_id)
        if cooperative_id is not None:
            statement = statement.where(Cooperative.id == cooperative_id)
        return await self.session.scalar(statement)

    async def list_scoped(
        self,
        cooperative_id: UUID | None,
        *,
        keyword: str | None,
        status: CooperativeStatus | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: SortDirection,
    ) -> tuple[list[Cooperative], int]:
        conditions = self._scope_conditions(cooperative_id)
        if keyword:
            pattern = f"%{keyword.strip()}%"
            conditions.append(
                or_(Cooperative.code.ilike(pattern), Cooperative.name.ilike(pattern))
            )
        if status is not None:
            conditions.append(Cooperative.status == status)

        base_statement: Select[tuple[Cooperative]] = select(Cooperative).where(
            *conditions
        )
        total = await self.session.scalar(
            select(func.count(Cooperative.id)).where(*conditions)
        )
        sort_column = {
            "code": Cooperative.code,
            "name": Cooperative.name,
            "createdAt": Cooperative.created_at,
            "created_at": Cooperative.created_at,
        }.get(sort_by, Cooperative.created_at)
        ordering = (
            desc(sort_column)
            if sort_order is SortDirection.DESC
            else asc(sort_column)
        )
        result = await self.session.scalars(
            base_statement.order_by(ordering, Cooperative.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def add(self, cooperative: Cooperative) -> Cooperative:
        self.session.add(cooperative)
        await self.session.flush()
        return cooperative

    async def update(
        self,
        cooperative: Cooperative,
        values: dict[str, object],
    ) -> Cooperative:
        for field, value in values.items():
            setattr(cooperative, field, value)
        await self.session.flush()
        return cooperative

    @staticmethod
    def _scope_conditions(
        cooperative_id: UUID | None,
    ) -> list[ColumnElement[bool]]:
        return (
            [Cooperative.id == cooperative_id]
            if cooperative_id is not None
            else []
        )


__all__ = ["CooperativeRepository"]
