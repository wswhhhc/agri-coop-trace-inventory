from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import permission_denied, resource_not_found
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.infrastructure.transaction import transaction_scope
from app.models import Permission, Role
from app.repositories.role import RoleRepository
from app.schemas.role import RolePermissionsUpdate


class RoleService:
    """系统管理员角色和权限查询、绑定用例。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = RoleRepository(session)

    async def list_roles(self, context: AuthContext) -> list[Role]:
        self._require_system_admin(context)
        async with transaction_scope(self.session):
            return await self.repository.list_with_permissions()

    async def list_permissions(self, context: AuthContext) -> list[Permission]:
        self._require_system_admin(context)
        async with transaction_scope(self.session):
            return await self.repository.list_permissions()

    async def update_permissions(
        self,
        context: AuthContext,
        role_id: UUID,
        payload: RolePermissionsUpdate,
    ) -> Role:
        self._require_system_admin(context)
        if len(set(payload.permission_codes)) != len(payload.permission_codes):
            raise AppException(
                code="BAD_REQUEST",
                message="权限编码不能重复",
                status_code=400,
            )
        async with transaction_scope(self.session):
            role = await self.repository.get_by_id_with_permissions(role_id)
            if role is None:
                raise resource_not_found()
            permissions = await self.repository.list_permissions()
            permissions_by_code = {permission.code: permission for permission in permissions}
            missing = set(payload.permission_codes) - permissions_by_code.keys()
            if missing:
                raise resource_not_found()
            return await self.repository.replace_permissions(
                role,
                [permissions_by_code[code] for code in payload.permission_codes],
            )

    @staticmethod
    def _require_system_admin(context: AuthContext) -> None:
        if context.role_code != "SYSTEM_ADMIN":
            raise permission_denied()


__all__ = ["RoleService"]
