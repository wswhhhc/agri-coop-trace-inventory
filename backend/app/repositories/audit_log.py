from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog

if TYPE_CHECKING:
    from app.core.audit.service import AuditEvent


class AuditLogRepository:
    """不可变审计日志写入仓储。"""

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


__all__ = ["AuditLogRepository"]
