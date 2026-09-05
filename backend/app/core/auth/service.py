"""认证上下文组装服务。"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import jwt
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.context import AuthContext
from app.core.auth.session import RedisSessionStore
from app.core.config import Settings
from app.core.exceptions import AppException
from app.core.security import decode_jwt
from app.models import SYSTEM_ADMIN_ROLE_CODE, User
from app.repositories.user import UserRepository
from app.repositories.warehouse import WarehouseRepository

COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"


class AuthService:
    """从令牌和最新数据库状态创建认证上下文。"""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        session_store: RedisSessionStore | None = None,
    ) -> None:
        self.user_repository = UserRepository(session)
        self.warehouse_repository = WarehouseRepository(session)
        self.settings = settings
        self.session_store = session_store

    async def build_context(self, token: str) -> AuthContext:
        """校验访问令牌并返回当前有效的认证上下文。"""
        claims = self._decode_token(token)
        user_id = self._claim_uuid(claims, "sub")
        session_id = self._claim_string(claims, "sid")
        if self.session_store is not None:
            try:
                auth_session = await self.session_store.get(session_id)
            except RedisError as exc:
                raise _dependency_unavailable() from exc
            if auth_session is None or auth_session.user_id != user_id:
                raise _unauthorized("AUTHENTICATION_REQUIRED", "会话已失效")
        user = await self.user_repository.get_by_id_with_access(user_id)

        if user is None:
            raise _unauthorized("AUTHENTICATION_REQUIRED", "用户不存在或身份已失效")
        if user.status != "ACTIVE":
            raise _unauthorized("ACCOUNT_DISABLED", "用户已被禁用")
        if user.role is None:
            raise _unauthorized("AUTHENTICATION_REQUIRED", "用户角色无效")

        cooperative_id = user.cooperative_id
        if user.role.code != SYSTEM_ADMIN_ROLE_CODE:
            if cooperative_id is None or user.cooperative is None:
                raise _unauthorized("AUTHENTICATION_REQUIRED", "用户合作社范围无效")
            if user.cooperative.status != "ACTIVE":
                raise _unauthorized("ACCOUNT_DISABLED", "合作社已被停用")

        warehouse_ids = await self._resolve_warehouse_scope(user)
        permission_codes = frozenset(
            permission.code for permission in user.role.permissions
        )

        return AuthContext(
            user_id=user.id,
            username=user.username,
            real_name=user.real_name,
            role_code=user.role.code,
            permission_codes=permission_codes,
            cooperative_id=cooperative_id,
            warehouse_ids=warehouse_ids,
            session_id=session_id,
            token_id=self._claim_string(claims, "jti"),
        )

    def _decode_token(self, token: str) -> dict[str, Any]:
        try:
            return decode_jwt(
                token,
                secret_key=self.settings.jwt_secret_key.get_secret_value(),
                algorithm=self.settings.jwt_algorithm,
                issuer=self.settings.jwt_issuer,
                audience=self.settings.jwt_audience,
            )
        except jwt.ExpiredSignatureError as exc:
            raise _unauthorized("TOKEN_EXPIRED", "访问令牌已过期") from exc
        except jwt.PyJWTError as exc:
            raise _unauthorized("AUTHENTICATION_REQUIRED", "访问令牌无效") from exc

    async def _resolve_warehouse_scope(self, user: User) -> frozenset[UUID] | None:
        assert user.role is not None
        if user.role.code == SYSTEM_ADMIN_ROLE_CODE:
            return None
        if user.role.code == COOPERATIVE_ADMIN_ROLE_CODE:
            assert user.cooperative_id is not None
            warehouses = await self.warehouse_repository.list_by_cooperative(
                user.cooperative_id
            )
        else:
            warehouses = await self.user_repository.list_authorized_warehouses(user.id)
        return frozenset(warehouse.id for warehouse in warehouses)

    @staticmethod
    def _claim_string(claims: dict[str, Any], name: str) -> str:
        value = claims.get(name)
        if not isinstance(value, str) or not value.strip():
            raise _unauthorized("AUTHENTICATION_REQUIRED", "访问令牌无效")
        return value

    @classmethod
    def _claim_uuid(cls, claims: dict[str, Any], name: str) -> UUID:
        value = cls._claim_string(claims, name)
        try:
            return UUID(value)
        except ValueError as exc:
            raise _unauthorized("AUTHENTICATION_REQUIRED", "访问令牌无效") from exc


def _unauthorized(code: str, message: str) -> AppException:
    return AppException(
        code=code,
        message=message,
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _dependency_unavailable() -> AppException:
    return AppException(
        code="DEPENDENCY_UNAVAILABLE",
        message="认证依赖服务暂时不可用",
        status_code=503,
    )


__all__ = ["COOPERATIVE_ADMIN_ROLE_CODE", "AuthService"]
