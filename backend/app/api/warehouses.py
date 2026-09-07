from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._cache import get_reference_query_cache
from app.api._pagination import build_pagination_meta
from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.schemas.common import ApiResponse, ListResponse
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseData,
    WarehouseListParams,
    WarehouseUpdate,
)
from app.services.query_cache import QueryCache
from app.services.reference_cache_policy import is_cacheable_reference_list
from app.services.warehouse import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


def get_warehouse_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WarehouseService:
    return WarehouseService(session)


@router.get("", response_model=ListResponse[WarehouseData])
async def list_warehouses(
    params: Annotated[WarehouseListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
    cache: Annotated[QueryCache, Depends(get_reference_query_cache)],
) -> ListResponse[WarehouseData]:
    service.ensure_read_access(context)
    if not is_cacheable_reference_list(params):
        items, total = await service.list(context, params)
        return ListResponse(
            data=[WarehouseData.model_validate(item) for item in items],
            pagination=build_pagination_meta(total, params.page, params.page_size),
        )

    key = cache.key("warehouse-list", context, params.model_dump(mode="json", by_alias=True))

    async def load() -> ListResponse[WarehouseData]:
        items, total = await service.list(context, params)
        return ListResponse(
            data=[WarehouseData.model_validate(item) for item in items],
            pagination=build_pagination_meta(total, params.page, params.page_size),
        )

    response = await cache.get_or_set(key, ListResponse[WarehouseData], load)
    return response if response is not None else await load()


@router.post("", response_model=ApiResponse[WarehouseData], status_code=201)
async def create_warehouse(
    payload: WarehouseCreate,
    context: CurrentAuthContext,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
    cache: Annotated[QueryCache, Depends(get_reference_query_cache)],
) -> ApiResponse[WarehouseData]:
    warehouse = await service.create(context, payload)
    await cache.invalidate_resource("warehouse-list", warehouse.cooperative_id)
    return ApiResponse(data=WarehouseData.model_validate(warehouse))


@router.get("/{warehouseId}", response_model=ApiResponse[WarehouseData])
async def get_warehouse(
    warehouse_id: Annotated[UUID, Path(alias="warehouseId")],
    context: CurrentAuthContext,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
    cache: Annotated[QueryCache, Depends(get_reference_query_cache)],
) -> ApiResponse[WarehouseData]:
    service.ensure_detail_read_scope(context, warehouse_id)
    key = cache.key("warehouse-detail", context, {"id": warehouse_id})

    async def load() -> ApiResponse[WarehouseData]:
        return ApiResponse(
            data=WarehouseData.model_validate(await service.get(context, warehouse_id))
        )

    response = await cache.get_or_set(key, ApiResponse[WarehouseData], load)
    return response if response is not None else await load()


@router.patch("/{warehouseId}", response_model=ApiResponse[WarehouseData])
async def update_warehouse(
    warehouse_id: Annotated[UUID, Path(alias="warehouseId")],
    payload: WarehouseUpdate,
    context: CurrentAuthContext,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
    cache: Annotated[QueryCache, Depends(get_reference_query_cache)],
) -> ApiResponse[WarehouseData]:
    warehouse = await service.update(context, warehouse_id, payload)
    await cache.invalidate_resource("warehouse-list", warehouse.cooperative_id)
    await cache.invalidate_resource("warehouse-detail", warehouse.cooperative_id)
    return ApiResponse(data=WarehouseData.model_validate(warehouse))


__all__ = ["get_warehouse_service", "router"]
