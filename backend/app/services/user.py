from __future__ import annotations

import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import (
    ensure_cooperative_scope,
    permission_denied,
    resource_not_found,
)
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.core.security import hash_password
from app.core.validation import require_non_empty_update
from app.infrastructure.transaction import transaction_scope
from app.models import (
    SYSTEM_ADMIN_ROLE_CODE,
    Cooperative,
    User,
    UserStatus,
)
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import (
    UserCreate,
    UserListParams,
    UserUpdate,
    WarehouseAssignment,
)

WAREHOUSE_STAFF_ROLE_CODE = "WAREHOUSE_STAFF"
COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
USER_MANAGE_PERMISSION = "user:manage"


class UserService:
    """用户和仓库授权业务用例。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)
        self.role_repository = RoleRepository(session)

    async def list_users(
        self,
        context: AuthContext,
        params: UserListParams,
    ) -> tuple[list[User], int]:
        self._require_manage(context)
        async with transaction_scope(self.session):
            return await self.repository.list_scoped(
                context.cooperative_id,
                keyword=params.keyword,
                role_code=params.role,
                status=params.status,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )

    async def get(self, context: AuthContext, user_id: UUID) -> User:
        if user_id != context.user_id:
            self._require_manage(context)
        async with transaction_scope(self.session):
            user = await self.repository.get_scoped(context.cooperative_id, user_id)
            if user is None:
                raise resource_not_found()
            return user

    async def create(
        self,
        context: AuthContext,
        payload: UserCreate,
    ) -> tuple[User, str]:
        self._require_manage(context)
        target_cooperative_id = payload.cooperative_id or context.cooperative_id
        async with transaction_scope(self.session):
            role = await self.role_repository.get_by_code_with_permissions(payload.role)
            if role is None:
                raise AppException(
                    code="BAD_REQUEST",
                    message="用户角色不存在",
                    status_code=400,
                )
            self._validate_role_assignment(context, role.code)
            self._validate_cooperative_assignment(role.code, target_cooperative_id)
            if target_cooperative_id is not None:
                ensure_cooperative_scope(context, target_cooperative_id)
                await self._require_active_cooperative(target_cooperative_id)
            self._validate_warehouse_payload(role.code, payload.warehouse_ids)
            if target_cooperative_id is None and payload.warehouse_ids:
                raise AppException(
                    code="BAD_REQUEST",
                    message="系统管理员用户不能绑定仓库",
                    status_code=400,
                )
            if target_cooperative_id is not None:
                await self._validate_warehouses(
                    target_cooperative_id, payload.warehouse_ids
                )

            initial_password = secrets.token_urlsafe(9)
            user = User(
                username=payload.username,
                real_name=payload.display_name,
                phone=payload.phone,
                cooperative_id=target_cooperative_id,
                role_id=role.id,
                password_hash=hash_password(initial_password),
                status=UserStatus.ACTIVE,
            )
            await self.repository.add(user)
            await self.repository.replace_warehouse_authorizations(
                user.id, payload.warehouse_ids
            )
            self.session.expire(user, ["user_warehouses"])
            loaded = await self.repository.get_scoped(
                target_cooperative_id, user.id
            )
            assert loaded is not None
            return loaded, initial_password

    async def update(
        self,
        context: AuthContext,
        user_id: UUID,
        payload: UserUpdate,
    ) -> User:
        self._require_manage(context)
        async with transaction_scope(self.session):
            user = await self.repository.get_scoped(context.cooperative_id, user_id)
            if user is None:
                raise resource_not_found()
            values: dict[str, object] = {}
            if payload.display_name is not None:
                values["real_name"] = payload.display_name
            if payload.phone is not None:
                values["phone"] = payload.phone
            if payload.status is not None:
                values["status"] = payload.status
            if payload.role is not None:
                role = await self.role_repository.get_by_code_with_permissions(
                    payload.role
                )
                if role is None:
                    raise AppException(
                        code="BAD_REQUEST",
                        message="用户角色不存在",
                        status_code=400,
                    )
                self._validate_role_assignment(context, role.code)
                self._validate_cooperative_assignment(
                    role.code, user.cooperative_id
                )
                values["role_id"] = role.id
            require_non_empty_update(values)
            await self.repository.update(user, values)
            loaded = await self.repository.get_scoped(
                context.cooperative_id, user.id
            )
            assert loaded is not None
            return loaded

    async def replace_warehouses(
        self,
        context: AuthContext,
        user_id: UUID,
        payload: WarehouseAssignment,
    ) -> User:
        self._require_manage(context)
        if context.role_code != COOPERATIVE_ADMIN_ROLE_CODE:
            raise permission_denied()
        async with transaction_scope(self.session):
            user = await self.repository.get_scoped(context.cooperative_id, user_id)
            if user is None:
                raise resource_not_found()
            if user.role is None or user.role.code != WAREHOUSE_STAFF_ROLE_CODE:
                raise AppException(
                    code="BAD_REQUEST",
                    message="只有仓库工作人员可以配置仓库授权",
                    status_code=400,
                )
            assert context.cooperative_id is not None
            await self._validate_warehouses(
                context.cooperative_id, payload.warehouse_ids
            )
            await self.repository.replace_warehouse_authorizations(
                user.id, payload.warehouse_ids
            )
            self.session.expire(user, ["user_warehouses"])
            loaded = await self.repository.get_scoped(
                context.cooperative_id, user.id
            )
            assert loaded is not None
            return loaded

    async def reset_password(
        self,
        context: AuthContext,
        user_id: UUID,
    ) -> tuple[User, str]:
        self._require_manage(context)
        async with transaction_scope(self.session):
            user = await self.repository.get_scoped(context.cooperative_id, user_id)
            if user is None:
                raise resource_not_found()
            temporary_password = secrets.token_urlsafe(9)
            await self.repository.update(
                user, {"password_hash": hash_password(temporary_password)}
            )
            return user, temporary_password

    async def _validate_warehouses(
        self,
        cooperative_id: UUID,
        warehouse_ids: list[UUID],
    ) -> None:
        if len(set(warehouse_ids)) != len(warehouse_ids):
            raise AppException(
                code="BAD_REQUEST",
                message="仓库授权列表不能包含重复项",
                status_code=400,
            )
        warehouses = await self.repository.list_warehouses_in_scope(
            cooperative_id, warehouse_ids
        )
        if len(warehouses) != len(warehouse_ids):
            raise resource_not_found()

    async def _require_active_cooperative(self, cooperative_id: UUID) -> None:
        cooperative = await self.session.get(Cooperative, cooperative_id)
        if cooperative is None:
            raise resource_not_found()
        if cooperative.status.value != "ACTIVE":
            raise AppException(
                code="ACCOUNT_DISABLED",
                message="合作社已被停用",
                status_code=403,
            )

    @staticmethod
    def _validate_role_assignment(context: AuthContext, role_code: str) -> None:
        if context.role_code == COOPERATIVE_ADMIN_ROLE_CODE and (
            role_code != WAREHOUSE_STAFF_ROLE_CODE
        ):
            raise permission_denied()

    @staticmethod
    def _validate_cooperative_assignment(
        role_code: str,
        cooperative_id: UUID | None,
    ) -> None:
        if role_code == SYSTEM_ADMIN_ROLE_CODE and cooperative_id is not None:
            raise AppException(
                code="BAD_REQUEST",
                message="系统管理员不能关联合作社",
                status_code=400,
            )
        if role_code != SYSTEM_ADMIN_ROLE_CODE and cooperative_id is None:
            raise AppException(
                code="BAD_REQUEST",
                message="非系统管理员必须关联合作社",
                status_code=400,
            )

    @staticmethod
    def _validate_warehouse_payload(
        role_code: str,
        warehouse_ids: list[UUID],
    ) -> None:
        if role_code != WAREHOUSE_STAFF_ROLE_CODE and warehouse_ids:
            raise AppException(
                code="BAD_REQUEST",
                message="只有仓库工作人员可以绑定仓库",
                status_code=400,
            )

    @staticmethod
    def _require_manage(context: AuthContext) -> None:
        if not context.has_permission(USER_MANAGE_PERMISSION) or context.role_code not in {
            SYSTEM_ADMIN_ROLE_CODE,
            COOPERATIVE_ADMIN_ROLE_CODE,
        }:
            raise permission_denied()


__all__ = ["UserService"]
