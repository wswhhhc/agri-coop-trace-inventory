from __future__ import annotations

from uuid import UUID

from app.core.auth.authorization import permission_denied
from app.core.auth.context import AuthContext

MODEL_READ_PERMISSION = "model:read"
MODEL_MANAGE_PERMISSION = "model:manage"
SYSTEM_ADMIN_ROLE_CODE = "SYSTEM_ADMIN"
COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
WAREHOUSE_STAFF_ROLE_CODE = "WAREHOUSE_STAFF"


def require_model_read(context: AuthContext) -> None:
    if context.role_code not in {
        SYSTEM_ADMIN_ROLE_CODE,
        COOPERATIVE_ADMIN_ROLE_CODE,
        WAREHOUSE_STAFF_ROLE_CODE,
    } or not context.has_permission(MODEL_READ_PERMISSION):
        raise permission_denied()


def require_model_manage(context: AuthContext) -> None:
    if context.role_code != COOPERATIVE_ADMIN_ROLE_CODE or not context.has_permission(
        MODEL_MANAGE_PERMISSION
    ):
        raise permission_denied()


def warehouse_ids_for_query(context: AuthContext) -> frozenset[UUID] | None:
    if context.role_code in {SYSTEM_ADMIN_ROLE_CODE, COOPERATIVE_ADMIN_ROLE_CODE}:
        return None
    return context.warehouse_ids


__all__ = [
    "MODEL_MANAGE_PERMISSION",
    "MODEL_READ_PERMISSION",
    "require_model_manage",
    "require_model_read",
    "warehouse_ids_for_query",
]
