from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models import TaskRecord


class TaskRepository:
    """跨业务异步任务的范围查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_scoped(
        self,
        task_id: UUID,
        cooperative_id: UUID | None,
        requester_id: UUID,
        can_manage: bool,
    ) -> TaskRecord | None:
        conditions: list[ColumnElement[bool]] = [TaskRecord.id == task_id]
        if cooperative_id is not None:
            conditions.append(TaskRecord.cooperative_id == cooperative_id)
        if not can_manage:
            conditions.append(TaskRecord.requested_by == requester_id)
        return await self.session.scalar(select(TaskRecord).where(*conditions))


__all__ = ["TaskRepository"]
