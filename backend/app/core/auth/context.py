"""当前请求的认证和数据范围上下文。"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuthContext:
    """由服务端数据库状态推导出的当前用户上下文。

    ``warehouse_ids`` 为 ``None`` 表示全局仓库范围（系统管理员），空集合
    表示当前用户没有可访问的仓库。业务代码不应直接信任 JWT 中的可变权限。
    """

    user_id: UUID
    username: str
    real_name: str
    role_code: str
    permission_codes: frozenset[str]
    cooperative_id: UUID | None
    warehouse_ids: frozenset[UUID] | None
    session_id: str
    token_id: str

    @property
    def is_global_scope(self) -> bool:
        """当前用户是否拥有全局合作社和仓库范围。"""
        return self.cooperative_id is None and self.warehouse_ids is None

    def has_permission(self, permission_code: str) -> bool:
        """判断当前用户是否拥有指定功能权限。"""
        return permission_code in self.permission_codes

    def has_cooperative_access(self, cooperative_id: UUID) -> bool:
        """判断当前用户是否可以访问指定合作社。"""
        return self.cooperative_id is None or self.cooperative_id == cooperative_id

    def has_warehouse_access(self, warehouse_id: UUID) -> bool:
        """判断当前用户是否可以访问指定仓库。"""
        return self.warehouse_ids is None or warehouse_id in self.warehouse_ids


__all__ = ["AuthContext"]
