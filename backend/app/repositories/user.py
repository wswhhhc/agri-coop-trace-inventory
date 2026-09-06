from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, asc, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.elements import ColumnElement

from app.models import (
    Role,
    SortDirection,
    User,
    UserStatus,
    UserWarehouse,
    Warehouse,
    WarehouseStatus,
)
from app.repositories._query_helpers import contains_pattern
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

    async def get_scoped(
        self,
        cooperative_id: UUID | None,
        target_id: UUID,
    ) -> User | None:
        statement = (
            select(User)
            .options(*self._access_options())
            .where(User.id == target_id)
        )
        if cooperative_id is not None:
            statement = statement.where(User.cooperative_id == cooperative_id)
        return await self.session.scalar(statement)

    async def list_scoped(
        self,
        cooperative_id: UUID | None,
        *,
        keyword: str | None,
        role_code: str | None,
        status: UserStatus | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: SortDirection,
    ) -> tuple[list[User], int]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(User.cooperative_id == cooperative_id)
        if keyword:
            pattern = contains_pattern(keyword)
            conditions.append(
                or_(User.username.ilike(pattern), User.real_name.ilike(pattern))
            )
        if role_code:
            conditions.append(User.role.has(code=role_code))
        if status is not None:
            conditions.append(User.status == status)

        statement: Select[tuple[User]] = (
            select(User).options(*self._access_options()).where(*conditions)
        )
        total = await self.session.scalar(select(func.count(User.id)).where(*conditions))
        sort_column = {
            "username": User.username,
            "displayName": User.real_name,
            "real_name": User.real_name,
            "createdAt": User.created_at,
            "created_at": User.created_at,
        }.get(sort_by, User.created_at)
        ordering = (
            desc(sort_column)
            if sort_order is SortDirection.DESC
            else asc(sort_column)
        )
        result = await self.session.scalars(
            statement.order_by(ordering, User.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

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

    async def list_warehouses_in_scope(
        self,
        cooperative_id: UUID,
        warehouse_ids: list[UUID],
    ) -> list[Warehouse]:
        statement = (
            select(Warehouse)
            .where(Warehouse.cooperative_id == cooperative_id)
            .where(Warehouse.id.in_(warehouse_ids))
            .where(Warehouse.status == WarehouseStatus.ACTIVE)
        )
        result = await self.session.scalars(statement)
        return list(result)

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User, values: dict[str, object]) -> User:
        for field, value in values.items():
            setattr(user, field, value)
        await self.session.flush()
        return user

    async def replace_warehouse_authorizations(
        self,
        user_id: UUID,
        warehouse_ids: list[UUID],
    ) -> None:
        await self.session.execute(
            delete(UserWarehouse).where(UserWarehouse.user_id == user_id)
        )
        self.session.add_all(
            [
                UserWarehouse(user_id=user_id, warehouse_id=warehouse_id)
                for warehouse_id in warehouse_ids
            ]
        )
        await self.session.flush()


__all__ = ["UserRepository"]
