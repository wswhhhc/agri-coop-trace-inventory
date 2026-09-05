"""认证用户的功能权限和数据范围依赖。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Path

from app.core.auth.context import AuthContext
from app.core.auth.dependencies import CurrentAuthContext
from app.core.exceptions import AppException, DataScopeAccessDeniedError


def permission_denied() -> AppException:
    """创建统一的功能权限不足异常。"""
    return AppException(
        code="PERMISSION_DENIED",
        message="缺少执行该操作的权限",
        status_code=403,
    )


def resource_not_found() -> AppException:
    """创建统一的资源不可见异常。"""
    return AppException(
        code="RESOURCE_NOT_FOUND",
        message="资源不存在或不可见",
        status_code=404,
    )


def ensure_cooperative_scope(
    context: AuthContext,
    cooperative_id: UUID,
) -> None:
    """断言合作社属于当前认证上下文范围。"""
    if not context.has_cooperative_access(cooperative_id):
        raise DataScopeAccessDeniedError(resource_type="cooperative")


def ensure_warehouse_scope(
    context: AuthContext,
    warehouse_id: UUID,
) -> None:
    """断言仓库属于当前认证上下文范围。"""
    if not context.has_warehouse_access(warehouse_id):
        raise DataScopeAccessDeniedError(resource_type="warehouse")


def require_permission(
    permission_code: str,
) -> Callable[..., Awaitable[AuthContext]]:
    """创建一个要求指定功能权限的 FastAPI 依赖。"""

    async def dependency(context: CurrentAuthContext) -> AuthContext:
        if not context.has_permission(permission_code):
            raise permission_denied()
        return context

    return dependency


async def require_cooperative_scope(
    cooperative_id: Annotated[UUID, Path(alias="cooperativeId")],
    context: CurrentAuthContext,
) -> AuthContext:
    """校验路径合作社是否在当前认证上下文范围内。"""
    ensure_cooperative_scope(context, cooperative_id)
    return context


async def require_warehouse_scope(
    warehouse_id: Annotated[UUID, Path(alias="warehouseId")],
    context: CurrentAuthContext,
) -> AuthContext:
    """校验路径仓库是否在当前认证上下文范围内。"""
    ensure_warehouse_scope(context, warehouse_id)
    return context


__all__ = [
    "ensure_cooperative_scope",
    "ensure_warehouse_scope",
    "permission_denied",
    "require_cooperative_scope",
    "require_permission",
    "require_warehouse_scope",
    "resource_not_found",
]
