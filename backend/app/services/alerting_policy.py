from __future__ import annotations

from uuid import UUID

from app.core.auth.authorization import permission_denied
from app.core.auth.context import AuthContext

SYSTEM_ADMIN_ROLE_CODE = "SYSTEM_ADMIN"
COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
WAREHOUSE_STAFF_ROLE_CODE = "WAREHOUSE_STAFF"
ALERT_READ_PERMISSION = "alert:read"
ALERT_HANDLE_PERMISSION = "alert:handle"


def require_alert_read(context: AuthContext) -> None:
    if context.role_code not in {
        SYSTEM_ADMIN_ROLE_CODE,
        COOPERATIVE_ADMIN_ROLE_CODE,
        WAREHOUSE_STAFF_ROLE_CODE,
    } or not context.has_permission(ALERT_READ_PERMISSION):
        raise permission_denied()


def require_alert_handle(context: AuthContext) -> None:
    if context.role_code not in {
        COOPERATIVE_ADMIN_ROLE_CODE,
        WAREHOUSE_STAFF_ROLE_CODE,
    } or not context.has_permission(ALERT_HANDLE_PERMISSION):
        raise permission_denied()


def require_rule_manage(context: AuthContext) -> None:
    if context.role_code != COOPERATIVE_ADMIN_ROLE_CODE or not context.has_permission(ALERT_READ_PERMISSION):
        raise permission_denied()


def require_scan_submit(context: AuthContext) -> None:
    if context.role_code not in {SYSTEM_ADMIN_ROLE_CODE, COOPERATIVE_ADMIN_ROLE_CODE}:
        raise permission_denied()


def warehouse_ids_for_query(context: AuthContext) -> frozenset[UUID] | None:
    if context.role_code in {SYSTEM_ADMIN_ROLE_CODE, COOPERATIVE_ADMIN_ROLE_CODE}:
        return None
    return context.warehouse_ids


__all__ = [
    "ALERT_HANDLE_PERMISSION",
    "ALERT_READ_PERMISSION",
    "COOPERATIVE_ADMIN_ROLE_CODE",
    "SYSTEM_ADMIN_ROLE_CODE",
    "WAREHOUSE_STAFF_ROLE_CODE",
    "require_alert_handle",
    "require_alert_read",
    "require_rule_manage",
    "require_scan_submit",
    "warehouse_ids_for_query",
]
