from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.redaction import redact_detail
from app.core.auth.authorization import permission_denied, resource_not_found
from app.core.auth.context import AuthContext
from app.infrastructure.transaction import transaction_scope
from app.models import AuditLog
from app.repositories.audit_log import AuditLogRepository
from app.schemas.audit_log import AuditLogListParams

AUDIT_READ_PERMISSION = "audit:read"
SYSTEM_ADMIN_ROLE_CODE = "SYSTEM_ADMIN"
COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
WAREHOUSE_STAFF_ROLE_CODE = "WAREHOUSE_STAFF"
_AUDIT_READ_ROLES = {
    SYSTEM_ADMIN_ROLE_CODE,
    COOPERATIVE_ADMIN_ROLE_CODE,
    WAREHOUSE_STAFF_ROLE_CODE,
}


class AuditLogQueryService:
    """审计日志只读用例，按当前身份收紧数据范围。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AuditLogRepository(session)

    async def list(
        self,
        context: AuthContext,
        params: AuditLogListParams,
    ) -> tuple[list[AuditLog], int]:
        self._require_read_permission(context)
        async with transaction_scope(self.session):
            return await self.repository.list_scoped(
                context.cooperative_id,
                self._scoped_user_id(context, params.user_id),
                action=params.action,
                resource_type=params.resource_type,
                resource_id=params.resource_id,
                result=params.result,
                start_date=params.start_date,
                end_date=params.end_date,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )

    async def get(self, context: AuthContext, audit_log_id: UUID) -> AuditLog:
        self._require_read_permission(context)
        async with transaction_scope(self.session):
            record = await self.repository.get_scoped(
                context.cooperative_id,
                self._scoped_user_id(context, None),
                audit_log_id,
            )
        if record is None:
            raise resource_not_found()
        return record

    @staticmethod
    def _require_read_permission(context: AuthContext) -> None:
        if (
            context.role_code not in _AUDIT_READ_ROLES
            or not context.has_permission(AUDIT_READ_PERMISSION)
        ):
            raise permission_denied()

    @staticmethod
    def _scoped_user_id(
        context: AuthContext,
        requested_user_id: UUID | None,
    ) -> UUID | None:
        if context.role_code == WAREHOUSE_STAFF_ROLE_CODE:
            return context.user_id
        return requested_user_id


def audit_log_data(record: AuditLog) -> dict[str, Any]:
    """构造对外审计投影，明确排除 IP 地址和 User-Agent。"""
    return {
        "id": record.id,
        "cooperative_id": record.cooperative_id,
        "user_id": record.user_id,
        "action": record.action,
        "module": record.module,
        "resource_type": record.object_type,
        "resource_id": record.object_id,
        "result": record.result,
        "request_id": record.request_id,
        "detail": redact_detail(record.detail),
        "created_at": record.created_at,
    }


__all__ = ["AUDIT_READ_PERMISSION", "AuditLogQueryService", "audit_log_data"]
