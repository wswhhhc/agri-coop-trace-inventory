from __future__ import annotations

from app.core.auth.authorization import permission_denied
from app.core.auth.context import AuthContext
from app.schemas.export import ReportType

COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"


def require_export(context: AuthContext, report_type: ReportType) -> None:
    """导出属于合作社经营报表能力，仅合作社管理员可执行。"""
    permission = (
        "inventory:read" if report_type is ReportType.INVENTORY_DETAIL else "alert:read"
    )
    if (
        context.role_code != COOPERATIVE_ADMIN_ROLE_CODE
        or context.cooperative_id is None
        or not context.has_permission(permission)
    ):
        raise permission_denied()


__all__ = ["COOPERATIVE_ADMIN_ROLE_CODE", "require_export"]
