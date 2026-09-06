from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.schemas.common import ApiResponse, ListResponse
from app.schemas.role import PermissionData, RoleData, RolePermissionsUpdate
from app.services.role import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


def get_role_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RoleService:
    return RoleService(session)


def _role_data(role) -> RoleData:
    return RoleData(
        id=role.id,
        code=role.code,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        permissions=[PermissionData.model_validate(permission) for permission in role.permissions],
    )


@router.get("", response_model=ListResponse[RoleData])
async def list_roles(
    context: CurrentAuthContext,
    service: Annotated[RoleService, Depends(get_role_service)],
) -> ListResponse[RoleData]:
    items = await service.list_roles(context)
    return ListResponse(
        data=[_role_data(item) for item in items],
        pagination={"page": 1, "pageSize": len(items) or 1, "totalItems": len(items), "totalPages": 1},
    )


@router.get("/permissions", response_model=ListResponse[PermissionData])
async def list_permissions(
    context: CurrentAuthContext,
    service: Annotated[RoleService, Depends(get_role_service)],
) -> ListResponse[PermissionData]:
    items = await service.list_permissions(context)
    return ListResponse(
        data=[PermissionData.model_validate(item) for item in items],
        pagination={"page": 1, "pageSize": len(items) or 1, "totalItems": len(items), "totalPages": 1},
    )


@router.put("/{roleId}/permissions", response_model=ApiResponse[RoleData])
async def update_role_permissions(
    role_id: Annotated[UUID, Path(alias="roleId")],
    payload: RolePermissionsUpdate,
    context: CurrentAuthContext,
    service: Annotated[RoleService, Depends(get_role_service)],
) -> ApiResponse[RoleData]:
    return ApiResponse(data=_role_data(await service.update_permissions(context, role_id, payload)))


__all__ = ["get_role_service", "router"]
