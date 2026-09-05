from __future__ import annotations

from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.models import User
from app.schemas.common import ApiResponse, ListResponse, PaginationMeta
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
        pagination=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=ceil(total / params.page_size) if total else 0,
        ),
    )


@router.post("", response_model=ApiResponse[UserCreateData], status_code=201)
async def create_user(
    payload: UserCreate,
    context: CurrentAuthContext,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse[UserCreateData]:
    user, initial_password = await service.create(context, payload)
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
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse[UserData]:
    return ApiResponse(data=_user_data(await service.update(context, user_id, payload)))


@router.put("/{userId}/warehouses", response_model=ApiResponse[UserData])
async def replace_user_warehouses(
    user_id: Annotated[UUID, Path(alias="userId")],
    payload: WarehouseAssignment,
    context: CurrentAuthContext,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse[UserData]:
    return ApiResponse(
        data=_user_data(
            await service.replace_warehouses(context, user_id, payload)
        )
    )


@router.post(
    "/{userId}/password-resets",
    response_model=ApiResponse[PasswordResetData],
)
async def reset_user_password(
    user_id: Annotated[UUID, Path(alias="userId")],
    context: CurrentAuthContext,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse[PasswordResetData]:
    _, temporary_password = await service.reset_password(context, user_id)
    return ApiResponse(data=PasswordResetData(temporary_password=temporary_password))


__all__ = ["get_user_service", "router"]
