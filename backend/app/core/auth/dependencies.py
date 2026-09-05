"""FastAPI 认证依赖。"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.service import AuditLogService
from app.core.auth.context import AuthContext
from app.core.auth.rate_limit import LoginRateLimiter
from app.core.auth.service import AuthService
from app.core.auth.session import RedisSessionStore
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.infrastructure import database as database_infrastructure
from app.infrastructure.database import get_db_session
from app.infrastructure.redis import get_redis_client


def get_session_store(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> RedisSessionStore:
    return RedisSessionStore(
        redis,
        key_prefix=settings.redis_key_prefix,
        ttl_seconds=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


def get_login_rate_limiter(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> LoginRateLimiter:
    return LoginRateLimiter(
        redis,
        key_prefix=settings.redis_key_prefix,
        max_attempts=settings.login_rate_limit_per_minute,
    )


def get_audit_log_service() -> AuditLogService:
    session_factory = database_infrastructure.SessionLocal
    if session_factory is None:
        raise RuntimeError("数据库尚未初始化")
    return AuditLogService(session_factory)


async def get_auth_context(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    session_store: Annotated[RedisSessionStore | None, Depends(get_session_store)] = None,
) -> AuthContext:
    """读取 Bearer Token 并构建当前请求的认证上下文。"""
    token = _extract_bearer_token(request.headers.get("Authorization"))
    return await AuthService(session, settings, session_store).build_context(token)


def _extract_bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise _missing_authentication()

    scheme, separator, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not separator or not token.strip():
        raise _missing_authentication()
    return token.strip()


def _missing_authentication() -> AppException:
    return AppException(
        code="AUTHENTICATION_REQUIRED",
        message="缺少有效身份信息",
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
    )


CurrentAuthContext = Annotated[AuthContext, Depends(get_auth_context)]


__all__ = [
    "CurrentAuthContext",
    "get_audit_log_service",
    "get_auth_context",
    "get_login_rate_limiter",
    "get_session_store",
]
