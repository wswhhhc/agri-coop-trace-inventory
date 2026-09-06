from __future__ import annotations

from uuid import UUID

from app.core.auth.authorization import ensure_warehouse_scope, permission_denied
from app.core.auth.context import AuthContext

SYSTEM_ADMIN_ROLE_CODE = "SYSTEM_ADMIN"
COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
WAREHOUSE_STAFF_ROLE_CODE = "WAREHOUSE_STAFF"
_DASHBOARD_ROLES = {
    SYSTEM_ADMIN_ROLE_CODE,
    COOPERATIVE_ADMIN_ROLE_CODE,
    WAREHOUSE_STAFF_ROLE_CODE,
}


def require_dashboard_read(context: AuthContext) -> None:
    """大屏基于库存读取权限开放给三类内部业务角色。"""
    if context.role_code not in _DASHBOARD_ROLES or not context.has_permission(
        "inventory:read"
    ):
        raise permission_denied()


def require_forecast_comparison(context: AuthContext) -> None:
    if context.role_code not in _DASHBOARD_ROLES or not context.has_permission(
        "model:read"
    ):
        raise permission_denied()


def ensure_dashboard_warehouse_scope(
    context: AuthContext, warehouse_id: UUID | None
) -> None:
    if warehouse_id is not None:
        ensure_warehouse_scope(context, warehouse_id)


def warehouse_ids_for_dashboard(context: AuthContext) -> frozenset[UUID] | None:
    if context.role_code in {SYSTEM_ADMIN_ROLE_CODE, COOPERATIVE_ADMIN_ROLE_CODE}:
        return None
    return context.warehouse_ids


__all__ = [
    "COOPERATIVE_ADMIN_ROLE_CODE",
    "SYSTEM_ADMIN_ROLE_CODE",
    "WAREHOUSE_STAFF_ROLE_CODE",
    "ensure_dashboard_warehouse_scope",
    "require_dashboard_read",
    "require_forecast_comparison",
    "warehouse_ids_for_dashboard",
]
