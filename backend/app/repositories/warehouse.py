from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserWarehouse, Warehouse


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
