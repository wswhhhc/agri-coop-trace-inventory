"""FastAPI 认证依赖。"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.context import AuthContext
from app.core.auth.service import AuthService
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.infrastructure.database import get_db_session


async def get_auth_context(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthContext:
    """读取 Bearer Token 并构建当前请求的认证上下文。"""
    token = _extract_bearer_token(request.headers.get("Authorization"))
    return await AuthService(session, settings).build_context(token)


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


__all__ = ["CurrentAuthContext", "get_auth_context"]
