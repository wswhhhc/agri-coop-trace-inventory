from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Permission, Role


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

    async def list_with_permissions(self) -> list[Role]:
        statement = select(Role).options(selectinload(Role.permissions)).order_by(Role.code)
        return list((await self.session.scalars(statement)).all())

    async def list_permissions(self) -> list[Permission]:
        statement = select(Permission).order_by(Permission.module, Permission.code)
        return list((await self.session.scalars(statement)).all())

    async def replace_permissions(
        self,
        role: Role,
        permissions: list[Permission],
    ) -> Role:
        role.permissions = permissions
        await self.session.flush()
        await self.session.refresh(role, attribute_names=["permissions"])
        return role


__all__ = ["RoleRepository"]
