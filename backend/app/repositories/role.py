from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Role


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


__all__ = ["RoleRepository"]
