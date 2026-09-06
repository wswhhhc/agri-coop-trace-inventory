from __future__ import annotations

from uuid import UUID

from app.core.auth.authorization import permission_denied
from app.core.auth.context import AuthContext
from app.models import SYSTEM_ADMIN_ROLE_CODE

COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
WAREHOUSE_STAFF_ROLE_CODE = "WAREHOUSE_STAFF"
BATCH_MANAGE_PERMISSION = "batch:manage"


def require_read_role(context: AuthContext) -> None:
    if context.role_code not in {
        SYSTEM_ADMIN_ROLE_CODE,
        COOPERATIVE_ADMIN_ROLE_CODE,
        WAREHOUSE_STAFF_ROLE_CODE,
    }:
        raise permission_denied()


def require_manage(context: AuthContext) -> None:
    if context.role_code not in {
        COOPERATIVE_ADMIN_ROLE_CODE,
        WAREHOUSE_STAFF_ROLE_CODE,
    } or not context.has_permission(BATCH_MANAGE_PERMISSION):
        raise permission_denied()


def warehouse_ids_for_query(context: AuthContext) -> frozenset[UUID] | None:
    if context.role_code in {
        SYSTEM_ADMIN_ROLE_CODE,
        COOPERATIVE_ADMIN_ROLE_CODE,
    }:
        return None
    return context.warehouse_ids


__all__ = [
    "BATCH_MANAGE_PERMISSION",
    "COOPERATIVE_ADMIN_ROLE_CODE",
    "WAREHOUSE_STAFF_ROLE_CODE",
    "require_manage",
    "require_read_role",
    "warehouse_ids_for_query",
]
