from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import resource_not_found
from app.core.auth.context import AuthContext
from app.infrastructure.transaction import transaction_scope
from app.models import TaskRecord
from app.repositories.task import TaskRepository
from app.services.task_policy import require_task_read


class TaskService:
    """统一异步任务状态读取，不负责任何具体任务执行。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TaskRepository(session)

    async def get(self, context: AuthContext, task_id: UUID) -> TaskRecord:
        can_manage = context.role_code in {"SYSTEM_ADMIN", "COOPERATIVE_ADMIN"}
        async with transaction_scope(self.session):
            task = await self.repository.get_scoped(
                task_id, context.cooperative_id, context.user_id, can_manage
            )
            if task is None:
                raise resource_not_found()
            require_task_read(context, task)
            return task


__all__ = ["TaskService"]
