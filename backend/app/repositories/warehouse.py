from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models import SortDirection, User, UserWarehouse, Warehouse, WarehouseStatus


class WarehouseRepository:
    """仓库及用户授权仓库查询仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, warehouse_id: UUID) -> Warehouse | None:
        return await self.session.get(Warehouse, warehouse_id)

    async def list_by_cooperative(
        self,
        cooperative_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Warehouse]:
        statement = (
            select(Warehouse)
            .where(Warehouse.cooperative_id == cooperative_id)
            .order_by(Warehouse.code)
        )
        if active_only:
            statement = statement.where(Warehouse.status == "ACTIVE")

        result = await self.session.scalars(statement)
        return list(result)

    async def get_scoped(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        target_id: UUID,
    ) -> Warehouse | None:
        statement = select(Warehouse).where(Warehouse.id == target_id)
        for condition in self._scope_conditions(cooperative_id, warehouse_ids):
            statement = statement.where(condition)
        return await self.session.scalar(statement)

    async def list_scoped(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        keyword: str | None,
        status: WarehouseStatus | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: SortDirection,
    ) -> tuple[list[Warehouse], int]:
        conditions = self._scope_conditions(cooperative_id, warehouse_ids)
        if keyword:
            pattern = f"%{keyword.strip()}%"
            conditions.append(
                or_(Warehouse.code.ilike(pattern), Warehouse.name.ilike(pattern))
            )
        if status is not None:
            conditions.append(Warehouse.status == status)

        statement: Select[tuple[Warehouse]] = select(Warehouse).where(*conditions)
        total = await self.session.scalar(
            select(func.count(Warehouse.id)).where(*conditions)
        )
        sort_column = {
            "code": Warehouse.code,
            "name": Warehouse.name,
            "createdAt": Warehouse.created_at,
            "created_at": Warehouse.created_at,
        }.get(sort_by, Warehouse.created_at)
        ordering = (
            desc(sort_column)
            if sort_order is SortDirection.DESC
            else asc(sort_column)
        )
        result = await self.session.scalars(
            statement.order_by(ordering, Warehouse.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def add(self, warehouse: Warehouse) -> Warehouse:
        self.session.add(warehouse)
        await self.session.flush()
        return warehouse

    async def update(
        self,
        warehouse: Warehouse,
        values: dict[str, object],
    ) -> Warehouse:
        for field, value in values.items():
            setattr(warehouse, field, value)
        await self.session.flush()
        return warehouse

    @staticmethod
    def _scope_conditions(
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(Warehouse.cooperative_id == cooperative_id)
        if warehouse_ids is not None:
            conditions.append(Warehouse.id.in_(warehouse_ids))
        return conditions

    async def list_authorized_for_user(
        self,
        user_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Warehouse]:
        """查询用户被授权且属于其合作社的仓库。"""
        statement: Select[tuple[Warehouse]] = (
            select(Warehouse)
            .join(UserWarehouse, UserWarehouse.warehouse_id == Warehouse.id)
            .join(User, User.id == UserWarehouse.user_id)
            .where(User.id == user_id)
            .where(
                (User.cooperative_id.is_(None))
                | (Warehouse.cooperative_id == User.cooperative_id)
            )
            .order_by(Warehouse.code)
        )
        if active_only:
            statement = statement.where(Warehouse.status == "ACTIVE")

        result = await self.session.scalars(statement)
        return list(result)


__all__ = ["WarehouseRepository"]
