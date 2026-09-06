from __future__ import annotations

from uuid import UUID

from app.core.auth.authorization import (
    ensure_warehouse_scope,
    permission_denied,
)
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException

SYSTEM_ADMIN_ROLE_CODE = "SYSTEM_ADMIN"
COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
WAREHOUSE_STAFF_ROLE_CODE = "WAREHOUSE_STAFF"
INVENTORY_READ_PERMISSION = "inventory:read"
INVENTORY_WRITE_PERMISSION = "inventory:write"

_READ_ROLES = {
    SYSTEM_ADMIN_ROLE_CODE,
    COOPERATIVE_ADMIN_ROLE_CODE,
    WAREHOUSE_STAFF_ROLE_CODE,
}
_WRITE_ROLES = {COOPERATIVE_ADMIN_ROLE_CODE, WAREHOUSE_STAFF_ROLE_CODE}


def require_cooperative(context: AuthContext) -> UUID:
    if context.cooperative_id is None:
        raise AppException(code="BAD_REQUEST", message="库存操作必须关联合作社", status_code=400)
    return context.cooperative_id


def require_read(context: AuthContext) -> None:
    if context.role_code not in _READ_ROLES or not context.has_permission(INVENTORY_READ_PERMISSION):
        raise permission_denied()


def require_write(context: AuthContext) -> None:
    if context.role_code not in _WRITE_ROLES or not context.has_permission(INVENTORY_WRITE_PERMISSION):
        raise permission_denied()


def warehouse_ids(context: AuthContext) -> frozenset[UUID] | None:
    if context.role_code in {SYSTEM_ADMIN_ROLE_CODE, COOPERATIVE_ADMIN_ROLE_CODE}:
        return None
    return context.warehouse_ids


def ensure_optional_warehouse_scope(
    context: AuthContext, warehouse_id: UUID | None
) -> None:
    if warehouse_id is not None and context.role_code == WAREHOUSE_STAFF_ROLE_CODE:
        ensure_warehouse_scope(context, warehouse_id)


__all__ = [
    "COOPERATIVE_ADMIN_ROLE_CODE",
    "INVENTORY_READ_PERMISSION",
    "INVENTORY_WRITE_PERMISSION",
    "SYSTEM_ADMIN_ROLE_CODE",
    "WAREHOUSE_STAFF_ROLE_CODE",
    "ensure_optional_warehouse_scope",
    "require_cooperative",
    "require_read",
    "require_write",
    "warehouse_ids",
]
