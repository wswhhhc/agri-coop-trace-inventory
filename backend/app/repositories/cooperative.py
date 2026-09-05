from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cooperative


class CooperativeRepository:
    """合作社查询仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, cooperative_id: UUID) -> Cooperative | None:
        return await self.session.get(Cooperative, cooperative_id)

    async def get_by_code(self, code: str) -> Cooperative | None:
        statement = select(Cooperative).where(Cooperative.code == code)
        return await self.session.scalar(statement)


__all__ = ["CooperativeRepository"]
