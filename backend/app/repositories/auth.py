from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.models import Cooperative, Permission, Role, User, UserWarehouse, Warehouse


class CooperativeRepository:
    """合作社查询仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, cooperative_id: UUID) -> Cooperative | None:
        return await self.session.get(Cooperative, cooperative_id)

    async def get_by_code(self, code: str) -> Cooperative | None:
        statement = select(Cooperative).where(Cooperative.code == code)
        return await self.session.scalar(statement)


class RoleRepository:
    """角色及其权限查询仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id_with_permissions(self, role_id: UUID) -> Role | None:
        statement = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return await self.session.scalar(statement)

    async def get_by_code_with_permissions(self, code: str) -> Role | None:
        statement = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.code == code)
        )
        return await self.session.scalar(statement)


class PermissionRepository:
    """权限查询仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_code(self, code: str) -> Permission | None:
        statement = select(Permission).where(Permission.code == code)
        return await self.session.scalar(statement)


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


__all__ = [
    "CooperativeRepository",
    "PermissionRepository",
    "RoleRepository",
    "UserRepository",
    "WarehouseRepository",
]
