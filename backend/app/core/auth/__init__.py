"""公共认证上下文模块。"""

from app.core.auth.authorization import (
    ensure_cooperative_scope,
    ensure_warehouse_scope,
    permission_denied,
    require_cooperative_scope,
    require_permission,
    require_warehouse_scope,
    resource_not_found,
)
from app.core.auth.context import AuthContext
from app.core.auth.dependencies import (
    CurrentAuthContext,
    get_auth_context,
    get_session_store,
)
from app.core.auth.service import AuthService

__all__ = [
    "AuthContext",
    "AuthService",
    "CurrentAuthContext",
    "ensure_cooperative_scope",
    "ensure_warehouse_scope",
    "get_auth_context",
    "get_session_store",
    "permission_denied",
    "require_cooperative_scope",
    "require_permission",
    "require_warehouse_scope",
    "resource_not_found",
]
