from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.models import Role, User, UserWarehouse, Warehouse
from app.repositories.warehouse import WarehouseRepository


class UserRepository:
    """用户及认证访问范围查询仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _access_options() -> tuple[ExecutableOption, ...]:
        return (
            selectinload(User.cooperative),
            selectinload(User.role),
            selectinload(User.role).selectinload(Role.permissions),
            selectinload(User.user_warehouses).selectinload(UserWarehouse.warehouse),
        )

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_id_with_access(self, user_id: UUID) -> User | None:
        statement = (
            select(User)
            .options(*self._access_options())
            .where(User.id == user_id)
        )
        return await self.session.scalar(statement)

    async def get_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return await self.session.scalar(statement)

    async def get_by_username_with_access(self, username: str) -> User | None:
        statement = (
            select(User)
            .options(*self._access_options())
            .where(User.username == username)
        )
        return await self.session.scalar(statement)

    async def list_authorized_warehouses(
        self,
        user_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Warehouse]:
        return await WarehouseRepository(self.session).list_authorized_for_user(
            user_id, active_only=active_only
        )


__all__ = ["UserRepository"]
