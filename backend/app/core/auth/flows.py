"""登录、刷新和退出的认证流程。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.context import AuditContext
from app.core.audit.service import AuditEvent, AuditLogService
from app.core.auth.rate_limit import LoginRateLimiter, RateLimitExceeded
from app.core.auth.session import (
    CreatedSession,
    InvalidRefreshToken,
    RedisSessionStore,
)
from app.core.config import Settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models import SYSTEM_ADMIN_ROLE_CODE, User
from app.models._common import utc_now
from app.repositories.user import UserRepository

_DUMMY_PASSWORD_HASH = hash_password("invalid-password-for-timing-equalization")


@dataclass(frozen=True, slots=True)
class AuthUserData:
    """可返回给前端的最小用户信息。"""

    user_id: UUID
    username: str
    display_name: str
    role: str
    cooperative_id: UUID | None
    status: str
    permissions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuthTokenResult:
    """认证流程返回的访问令牌、刷新令牌和用户信息。"""

    access_token: str
    expires_in: int
    refresh_token: str
    user: AuthUserData


class AuthenticationService:
    """执行认证状态校验和令牌签发。"""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        session_store: RedisSessionStore,
        login_rate_limiter: LoginRateLimiter | None = None,
        audit_log_service: AuditLogService | None = None,
    ) -> None:
        self.user_repository = UserRepository(session)
        self.settings = settings
        self.session_store = session_store
        self.login_rate_limiter = login_rate_limiter
        self.audit_log_service = audit_log_service

    async def login(
        self,
        username: str,
        password: str,
        client_ip: str = "unknown",
        audit_context: AuditContext | None = None,
    ) -> AuthTokenResult:
        """校验账号并创建 Redis 会话。"""
        await self._ensure_login_allowed(username, client_ip, audit_context)
        user = await self.user_repository.get_by_username_with_access(username)
        if user is None:
            verify_password(password, _DUMMY_PASSWORD_HASH)
            await self._record_login_failure(username, client_ip)
            await self._record_auth_event(
                context=audit_context,
                action="LOGIN",
                object_type="AUTHENTICATION",
                result="FAILURE",
                detail={"reason": "invalid_credentials"},
            )
            raise _invalid_credentials()

        if user.status == "LOCKED":
            await self._record_login_failure(username, client_ip)
            await self._record_auth_event(
                context=audit_context,
                action="LOGIN",
                object_type="AUTHENTICATION",
                result="FAILURE",
                user_id=user.id,
                cooperative_id=user.cooperative_id,
                detail={"reason": "account_locked"},
            )
            raise AppException(
                code="ACCOUNT_LOCKED",
                message="用户已被锁定",
                status_code=403,
            )
        if user.status != "ACTIVE":
            await self._record_login_failure(username, client_ip)
            await self._record_auth_event(
                context=audit_context,
                action="LOGIN",
                object_type="AUTHENTICATION",
                result="FAILURE",
                user_id=user.id,
                cooperative_id=user.cooperative_id,
                detail={"reason": "account_disabled"},
            )
            raise AppException(
                code="ACCOUNT_DISABLED",
                message="用户已被禁用",
                status_code=401,
            )
        if not verify_password(password, user.password_hash):
            await self._record_login_failure(username, client_ip)
            await self._record_auth_event(
                context=audit_context,
                action="LOGIN",
                object_type="AUTHENTICATION",
                result="FAILURE",
                user_id=user.id,
                cooperative_id=user.cooperative_id,
                detail={"reason": "invalid_credentials"},
            )
            raise _invalid_credentials()

        self._validate_user_scope(user)
        try:
            created = await self.session_store.create(user.id)
        except RedisError as exc:
            raise _dependency_unavailable() from exc

        user.last_login_at = utc_now()
        await self._reset_login_failures(username)
        await self._record_auth_event(
            context=audit_context,
            action="LOGIN",
            object_type="SESSION",
            result="SUCCESS",
            user_id=user.id,
            cooperative_id=user.cooperative_id,
            object_id=UUID(created.session.session_id),
        )
        return self._token_result(user, created)

    async def refresh(
        self,
        refresh_token: str,
        audit_context: AuditContext | None = None,
    ) -> AuthTokenResult:
        """轮换刷新令牌并签发新的访问令牌。"""
        try:
            created = await self.session_store.rotate(refresh_token)
        except InvalidRefreshToken as exc:
            await self._record_auth_event(
                context=audit_context,
                action="TOKEN_REFRESH",
                object_type="SESSION",
                result="FAILURE",
                detail={"reason": "invalid_refresh_token"},
            )
            raise _invalid_refresh_token() from exc
        except RedisError as exc:
            raise _dependency_unavailable() from exc

        user = await self.user_repository.get_by_id_with_access(created.session.user_id)
        try:
            if user is None:
                await self.session_store.revoke(created.session.session_id)
                await self._record_auth_event(
                    context=audit_context,
                    action="TOKEN_REFRESH",
                    object_type="SESSION",
                    result="FAILURE",
                    object_id=UUID(created.session.session_id),
                    detail={"reason": "user_not_found"},
                )
                raise _authentication_required()
            if user.status == "LOCKED":
                await self.session_store.revoke(created.session.session_id)
                await self._record_auth_event(
                    context=audit_context,
                    action="TOKEN_REFRESH",
                    object_type="SESSION",
                    result="FAILURE",
                    user_id=user.id,
                    cooperative_id=user.cooperative_id,
                    object_id=UUID(created.session.session_id),
                    detail={"reason": "account_locked"},
                )
                raise AppException(
                    code="ACCOUNT_LOCKED",
                    message="用户已被锁定",
                    status_code=403,
                )
            if user.status != "ACTIVE":
                await self.session_store.revoke(created.session.session_id)
                await self._record_auth_event(
                    context=audit_context,
                    action="TOKEN_REFRESH",
                    object_type="SESSION",
                    result="FAILURE",
                    user_id=user.id,
                    cooperative_id=user.cooperative_id,
                    object_id=UUID(created.session.session_id),
                    detail={"reason": "account_disabled"},
                )
                raise AppException(
                    code="ACCOUNT_DISABLED",
                    message="用户已被禁用",
                    status_code=401,
                )
            self._validate_user_scope(user)
        except RedisError as exc:
            raise _dependency_unavailable() from exc

        result = self._token_result(user, created)
        await self._record_auth_event(
            context=audit_context,
            action="TOKEN_REFRESH",
            object_type="SESSION",
            result="SUCCESS",
            user_id=user.id,
            cooperative_id=user.cooperative_id,
            object_id=UUID(created.session.session_id),
        )
        return result

    async def logout(
        self,
        refresh_token: str | None,
        audit_context: AuditContext | None = None,
    ) -> None:
        """撤销刷新令牌所属会话；没有令牌时保持幂等。"""
        if not refresh_token:
            await self._record_auth_event(
                context=audit_context,
                action="LOGOUT",
                object_type="SESSION",
                result="SUCCESS",
                detail={"reason": "no_refresh_token"},
            )
            return
        try:
            session_id = self.session_store.session_id_from_refresh_token(refresh_token)
        except InvalidRefreshToken:
            await self._record_auth_event(
                context=audit_context,
                action="LOGOUT",
                object_type="SESSION",
                result="FAILURE",
                detail={"reason": "invalid_refresh_token"},
            )
            return
        try:
            user_id = await self.session_store.revoke_by_refresh_token(refresh_token)
        except RedisError as exc:
            raise _dependency_unavailable() from exc
        await self._record_auth_event(
            context=audit_context,
            action="LOGOUT",
            object_type="SESSION",
            result="SUCCESS" if user_id is not None else "FAILURE",
            user_id=user_id,
            object_id=UUID(session_id),
            detail=(None if user_id is not None else {"reason": "invalid_refresh_token"}),
        )

    def _token_result(self, user: User, created: CreatedSession) -> AuthTokenResult:
        assert user.role is not None
        user_data = AuthUserData(
            user_id=user.id,
            username=user.username,
            display_name=user.real_name,
            role=user.role.code,
            cooperative_id=user.cooperative_id,
            status=user.status,
            permissions=tuple(sorted(permission.code for permission in user.role.permissions)),
        )
        access_token = create_access_token(
            subject=str(user.id),
            session_id=created.session.session_id,
            role=user.role.code,
            cooperative_id=(
                str(user.cooperative_id) if user.cooperative_id is not None else None
            ),
            secret_key=self.settings.jwt_secret_key.get_secret_value(),
            algorithm=self.settings.jwt_algorithm,
            expires_minutes=self.settings.access_token_expire_minutes,
            issuer=self.settings.jwt_issuer,
            audience=self.settings.jwt_audience,
        )
        return AuthTokenResult(
            access_token=access_token,
            expires_in=self.settings.access_token_expire_minutes * 60,
            refresh_token=created.refresh_token,
            user=user_data,
        )

    async def _ensure_login_allowed(
        self,
        username: str,
        client_ip: str,
        audit_context: AuditContext | None,
    ) -> None:
        if self.login_rate_limiter is None:
            return
        try:
            await self.login_rate_limiter.ensure_allowed(username, client_ip)
        except RateLimitExceeded as exc:
            await self._record_auth_event(
                context=audit_context,
                action="LOGIN",
                object_type="AUTHENTICATION",
                result="FAILURE",
                detail={"reason": "rate_limited"},
            )
            raise _rate_limit_exceeded(exc.retry_after) from exc
        except RedisError as exc:
            raise _dependency_unavailable() from exc

    async def _record_login_failure(self, username: str, client_ip: str) -> None:
        if self.login_rate_limiter is None:
            return
        try:
            await self.login_rate_limiter.record_failure(username, client_ip)
        except RateLimitExceeded as exc:
            raise _rate_limit_exceeded(exc.retry_after) from exc
        except RedisError as exc:
            raise _dependency_unavailable() from exc

    async def _reset_login_failures(self, username: str) -> None:
        if self.login_rate_limiter is None:
            return
        try:
            await self.login_rate_limiter.reset_account(username)
        except RedisError as exc:
            raise _dependency_unavailable() from exc

    async def _record_auth_event(
        self,
        *,
        context: AuditContext | None,
        action: str,
        object_type: str,
        result: str,
        cooperative_id: UUID | None = None,
        user_id: UUID | None = None,
        object_id: UUID | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        if self.audit_log_service is None:
            return
        try:
            await self.audit_log_service.record(
                AuditEvent.from_context(
                    context=context,
                    action=action,
                    object_type=object_type,
                    result=result,
                    cooperative_id=cooperative_id,
                    user_id=user_id,
                    object_id=object_id,
                    detail=detail,
                )
            )
        except (SQLAlchemyError, ValueError) as exc:
            raise _dependency_unavailable() from exc

    @staticmethod
    def _validate_user_scope(user: User) -> None:
        if user.role is None:
            raise _authentication_required()
        if user.role.code == SYSTEM_ADMIN_ROLE_CODE:
            return
        if user.cooperative_id is None or user.cooperative is None:
            raise _authentication_required()
        if user.cooperative.status != "ACTIVE":
            raise AppException(
                code="ACCOUNT_DISABLED",
                message="合作社已被停用",
                status_code=401,
            )


def _invalid_credentials() -> AppException:
    return AppException(
        code="INVALID_CREDENTIALS",
        message="用户名或密码错误",
        status_code=401,
    )


def _invalid_refresh_token() -> AppException:
    return AppException(
        code="INVALID_REFRESH_TOKEN",
        message="刷新令牌无效或已失效",
        status_code=401,
    )


def _authentication_required() -> AppException:
    return AppException(
        code="AUTHENTICATION_REQUIRED",
        message="缺少有效身份信息",
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _dependency_unavailable() -> AppException:
    return AppException(
        code="DEPENDENCY_UNAVAILABLE",
        message="认证依赖服务暂时不可用",
        status_code=503,
    )


def _rate_limit_exceeded(retry_after: int) -> AppException:
    return AppException(
        code="RATE_LIMIT_EXCEEDED",
        message="登录尝试过于频繁，请稍后重试",
        status_code=429,
        headers={"Retry-After": str(max(retry_after, 1))},
    )


__all__ = [
    "AuthTokenResult",
    "AuthUserData",
    "AuthenticationService",
]
