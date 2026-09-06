from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.core.audit.service import (
    AuditEvent,
    AuditLogService,
    audit_error_code,
    record_audit_safely,
)
from app.core.auth.dependencies import CurrentAuthContext, get_audit_log_service
from app.infrastructure.database import get_db_session
from app.models import User
from app.schemas.common import ApiResponse, ListResponse
from app.schemas.user import (
    PasswordResetData,
    UserCreate,
    UserCreateData,
    UserData,
    UserListParams,
    UserUpdate,
    WarehouseAssignment,
)
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserService:
    return UserService(session)


def _user_data(user: User) -> UserData:
    return UserData(
        id=user.id,
        username=user.username,
        display_name=user.real_name,
        role=user.role.code if user.role is not None else "",
        cooperative_id=user.cooperative_id,
        warehouse_ids=sorted(
            user_warehouse.warehouse_id for user_warehouse in user.user_warehouses
        ),
        phone=user.phone,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("", response_model=ListResponse[UserData])
async def list_users(
    params: Annotated[UserListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ListResponse[UserData]:
    users, total = await service.list_users(context, params)
    return ListResponse(
        data=[_user_data(user) for user in users],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@router.post("", response_model=ApiResponse[UserCreateData], status_code=201)
async def create_user(
    payload: UserCreate,
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[UserCreateData]:
    try:
        user, initial_password = await service.create(context, payload)
    except Exception as error:
        await _record_user_audit(
            audit_log_service,
            request,
            context,
            action="CREATE_USER",
            result="FAILURE",
            cooperative_id=context.cooperative_id,
            detail={"errorCode": audit_error_code(error)},
        )
        raise
    await _record_user_audit(
        audit_log_service,
        request,
        context,
        action="CREATE_USER",
        result="SUCCESS",
        cooperative_id=user.cooperative_id,
        object_id=user.id,
        detail={"username": user.username, "role": user.role.code},
    )
    data = UserCreateData(
        **_user_data(user).model_dump(),
        initial_password=initial_password,
    )
    return ApiResponse(data=data)


@router.get("/{userId}", response_model=ApiResponse[UserData])
async def get_user(
    user_id: Annotated[UUID, Path(alias="userId")],
    context: CurrentAuthContext,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse[UserData]:
    return ApiResponse(data=_user_data(await service.get(context, user_id)))


@router.patch("/{userId}", response_model=ApiResponse[UserData])
async def update_user(
    user_id: Annotated[UUID, Path(alias="userId")],
    payload: UserUpdate,
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[UserData]:
    try:
        user = await service.update(context, user_id, payload)
    except Exception as error:
        await _record_user_audit(
            audit_log_service,
            request,
            context,
            action="UPDATE_USER",
            result="FAILURE",
            cooperative_id=context.cooperative_id,
            object_id=user_id,
            detail={"errorCode": audit_error_code(error)},
        )
        raise
    await _record_user_audit(
        audit_log_service,
        request,
        context,
        action="UPDATE_USER",
        result="SUCCESS",
        cooperative_id=user.cooperative_id,
        object_id=user.id,
        detail={
            "updatedFields": sorted(payload.model_dump(exclude_unset=True).keys())
        },
    )
    return ApiResponse(data=_user_data(user))


@router.put("/{userId}/warehouses", response_model=ApiResponse[UserData])
async def replace_user_warehouses(
    user_id: Annotated[UUID, Path(alias="userId")],
    payload: WarehouseAssignment,
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[UserData]:
    try:
        user = await service.replace_warehouses(context, user_id, payload)
    except Exception as error:
        await _record_user_audit(
            audit_log_service,
            request,
            context,
            action="REPLACE_USER_WAREHOUSES",
            result="FAILURE",
            cooperative_id=context.cooperative_id,
            object_id=user_id,
            detail={"errorCode": audit_error_code(error)},
        )
        raise
    await _record_user_audit(
        audit_log_service,
        request,
        context,
        action="REPLACE_USER_WAREHOUSES",
        result="SUCCESS",
        cooperative_id=user.cooperative_id,
        object_id=user.id,
        detail={"warehouseCount": len(payload.warehouse_ids)},
    )
    return ApiResponse(data=_user_data(user))


@router.post(
    "/{userId}/password-resets",
    response_model=ApiResponse[PasswordResetData],
)
async def reset_user_password(
    user_id: Annotated[UUID, Path(alias="userId")],
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[PasswordResetData]:
    try:
        user, temporary_password = await service.reset_password(context, user_id)
    except Exception as error:
        await _record_user_audit(
            audit_log_service,
            request,
            context,
            action="RESET_USER_PASSWORD",
            result="FAILURE",
            cooperative_id=context.cooperative_id,
            object_id=user_id,
            detail={"errorCode": audit_error_code(error)},
        )
        raise
    await _record_user_audit(
        audit_log_service,
        request,
        context,
        action="RESET_USER_PASSWORD",
        result="SUCCESS",
        cooperative_id=user.cooperative_id,
        object_id=user.id,
        detail={"passwordReset": True},
    )
    return ApiResponse(data=PasswordResetData(temporary_password=temporary_password))


async def _record_user_audit(
    audit_log_service: AuditLogService,
    request: Request,
    context,
    *,
    action: str,
    result: str,
    cooperative_id: UUID | None,
    object_id: UUID | None = None,
    detail: dict[str, object] | None = None,
) -> None:
    await record_audit_safely(
        audit_log_service,
        AuditEvent(
            action=action,
            module="USER",
            object_type="USER",
            result=result,
            cooperative_id=cooperative_id,
            user_id=context.user_id,
            object_id=object_id,
            request_id=getattr(request.state, "request_id", None),
            detail=detail or {},
        ),
        logger,
    )


__all__ = ["get_user_service", "router"]
