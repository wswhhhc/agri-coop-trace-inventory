from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models import AuditLog, SortDirection

if TYPE_CHECKING:
    from app.core.audit.service import AuditEvent


class AuditLogRepository:
    """不可变审计日志仓储，仅提供新增和受限读取。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, event: AuditEvent) -> AuditLog:
        audit_log = AuditLog(
            cooperative_id=event.cooperative_id,
            user_id=event.user_id,
            action=event.action,
            module=event.module,
            object_type=event.object_type,
            object_id=event.object_id,
            result=event.result,
            request_id=event.request_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            detail=dict(event.detail),
            created_at=event.created_at,
        )
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log

    async def list_scoped(
        self,
        cooperative_id: UUID | None,
        user_id: UUID | None,
        *,
        action: str | None,
        resource_type: str | None,
        resource_id: UUID | None,
        result: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: SortDirection,
    ) -> tuple[list[AuditLog], int]:
        conditions = self._scope_conditions(cooperative_id, user_id)
        if action is not None:
            conditions.append(AuditLog.action == action)
        if resource_type is not None:
            conditions.append(AuditLog.object_type == resource_type)
        if resource_id is not None:
            conditions.append(AuditLog.object_id == resource_id)
        if result is not None:
            conditions.append(AuditLog.result == result)
        if start_date is not None:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date is not None:
            conditions.append(AuditLog.created_at <= end_date)

        total = await self.session.scalar(
            select(func.count(AuditLog.id)).where(*conditions)
        )
        sort_column = {
            "action": AuditLog.action,
            "module": AuditLog.module,
            "result": AuditLog.result,
            "createdAt": AuditLog.created_at,
            "created_at": AuditLog.created_at,
        }.get(sort_by, AuditLog.created_at)
        ordering = (
            desc(sort_column)
            if sort_order is SortDirection.DESC
            else asc(sort_column)
        )
        records = await self.session.scalars(
            select(AuditLog)
            .where(*conditions)
            .order_by(ordering, AuditLog.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(records), int(total or 0)

    async def get_scoped(
        self,
        cooperative_id: UUID | None,
        user_id: UUID | None,
        audit_log_id: UUID,
    ) -> AuditLog | None:
        return await self.session.scalar(
            select(AuditLog)
            .where(AuditLog.id == audit_log_id)
            .where(*self._scope_conditions(cooperative_id, user_id))
        )

    @staticmethod
    def _scope_conditions(
        cooperative_id: UUID | None,
        user_id: UUID | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(AuditLog.cooperative_id == cooperative_id)
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        return conditions


__all__ = ["AuditLogRepository"]
