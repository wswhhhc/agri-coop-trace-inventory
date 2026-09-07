from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._cache import get_permission_query_cache
from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.schemas.common import ApiResponse, ListResponse, PaginationMeta
from app.schemas.role import PermissionData, RoleData, RolePermissionsUpdate
from app.services.query_cache import QueryCache
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
    cache: Annotated[QueryCache, Depends(get_permission_query_cache)],
) -> ListResponse[RoleData]:
    RoleService.ensure_system_admin(context)
    key = cache.key("role-list", context)

    async def load() -> ListResponse[RoleData]:
        items = await service.list_roles(context)
        return ListResponse(
            data=[_role_data(item) for item in items],
            pagination=PaginationMeta(
                page=1,
                page_size=len(items) or 1,
                total_items=len(items),
                total_pages=1,
            ),
        )

    response = await cache.get_or_set(key, ListResponse[RoleData], load)
    return response if response is not None else await load()


@router.get("/permissions", response_model=ListResponse[PermissionData])
async def list_permissions(
    context: CurrentAuthContext,
    service: Annotated[RoleService, Depends(get_role_service)],
    cache: Annotated[QueryCache, Depends(get_permission_query_cache)],
) -> ListResponse[PermissionData]:
    RoleService.ensure_system_admin(context)
    key = cache.key("permission-list", context)

    async def load() -> ListResponse[PermissionData]:
        items = await service.list_permissions(context)
        return ListResponse(
            data=[PermissionData.model_validate(item) for item in items],
            pagination=PaginationMeta(
                page=1,
                page_size=len(items) or 1,
                total_items=len(items),
                total_pages=1,
            ),
        )

    response = await cache.get_or_set(key, ListResponse[PermissionData], load)
    return response if response is not None else await load()


@router.put("/{roleId}/permissions", response_model=ApiResponse[RoleData])
async def update_role_permissions(
    role_id: Annotated[UUID, Path(alias="roleId")],
    payload: RolePermissionsUpdate,
    context: CurrentAuthContext,
    service: Annotated[RoleService, Depends(get_role_service)],
    cache: Annotated[QueryCache, Depends(get_permission_query_cache)],
) -> ApiResponse[RoleData]:
    role = await service.update_permissions(context, role_id, payload)
    await cache.invalidate_resource("role-list", None)
    await cache.invalidate_resource("permission-list", None)
    return ApiResponse(data=_role_data(role))


__all__ = ["get_role_service", "router"]
