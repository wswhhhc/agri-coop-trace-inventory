"""认证 HTTP 接口。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.context import AuditContext
from app.core.audit.service import AuditLogService
from app.core.auth.dependencies import (
    CurrentAuthContext,
    get_audit_log_service,
    get_login_rate_limiter,
    get_session_store,
)
from app.core.auth.flows import AuthenticationService, AuthTokenResult
from app.core.auth.rate_limit import LoginRateLimiter
from app.core.auth.session import RedisSessionStore
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.infrastructure.database import get_transactional_session
from app.schemas.auth import (
    AuthTokenData,
    AuthTokenResponse,
    AuthUser,
    CurrentUserData,
    LoginRequest,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def get_authentication_service(
    session: Annotated[AsyncSession, Depends(get_transactional_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    session_store: Annotated[RedisSessionStore, Depends(get_session_store)],
    login_rate_limiter: Annotated[
        LoginRateLimiter, Depends(get_login_rate_limiter)
    ],
    audit_log_service: Annotated[
        AuditLogService, Depends(get_audit_log_service)
    ],
) -> AuthenticationService:
    return AuthenticationService(
        session,
        settings,
        session_store,
        login_rate_limiter,
        audit_log_service,
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> AuthTokenResponse:
    client_ip = request.client.host if request.client is not None else "unknown"
    result = await service.login(
        payload.username,
        payload.password,
        client_ip,
        AuditContext.from_request(request),
    )
    _set_refresh_cookie(response, service.settings, result.refresh_token)
    return AuthTokenResponse(data=_token_data(result))


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(
    request: Request,
    response: Response,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> AuthTokenResponse:
    refresh_token = request.cookies.get(service.settings.refresh_token_cookie_name)
    if not refresh_token:
        raise AppException(
            code="INVALID_REFRESH_TOKEN",
            message="刷新令牌无效或已失效",
            status_code=401,
        )
    result = await service.refresh(
        refresh_token,
        AuditContext.from_request(request),
    )
    _set_refresh_cookie(response, service.settings, result.refresh_token)
    return AuthTokenResponse(data=_token_data(result))


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> Response:
    refresh_token = request.cookies.get(service.settings.refresh_token_cookie_name)
    await service.logout(refresh_token, AuditContext.from_request(request))
    response.delete_cookie(
        key=service.settings.refresh_token_cookie_name,
        path=service.settings.refresh_token_cookie_path,
        domain=service.settings.refresh_token_cookie_domain,
    )
    response.status_code = 204
    return response


@router.get("/me", response_model=ApiResponse[CurrentUserData])
async def me(context: CurrentAuthContext) -> ApiResponse[CurrentUserData]:
    return ApiResponse(
        data=CurrentUserData(
            id=context.user_id,
            username=context.username,
            display_name=context.real_name,
            role=context.role_code,
            cooperative_id=context.cooperative_id,
            warehouse_ids=(
                sorted(context.warehouse_ids)
                if context.warehouse_ids is not None
                else None
            ),
            permissions=sorted(context.permission_codes),
            status="ACTIVE",
        )
    )


def _token_data(result: AuthTokenResult) -> AuthTokenData:
    return AuthTokenData(
        access_token=result.access_token,
        token_type="Bearer",
        expires_in=result.expires_in,
        user=AuthUser(
            id=result.user.user_id,
            username=result.user.username,
            display_name=result.user.display_name,
            role=result.user.role,
            cooperative_id=result.user.cooperative_id,
            status=result.user.status,
        ),
        permissions=list(result.user.permissions),
    )


def _set_refresh_cookie(response: Response, settings: Settings, token: str) -> None:
    ttl_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=token,
        max_age=ttl_seconds,
        expires=ttl_seconds,
        path=settings.refresh_token_cookie_path,
        domain=settings.refresh_token_cookie_domain,
        secure=settings.refresh_token_cookie_secure,
        httponly=True,
        samesite=settings.refresh_token_cookie_samesite,
    )


__all__ = ["get_authentication_service", "router"]
