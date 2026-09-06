from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

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
) -> ListResponse[WarehouseData]:
    items, total = await service.list(context, params)
    return ListResponse(
        data=[WarehouseData.model_validate(item) for item in items],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@router.post("", response_model=ApiResponse[WarehouseData], status_code=201)
async def create_warehouse(
    payload: WarehouseCreate,
    context: CurrentAuthContext,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> ApiResponse[WarehouseData]:
    return ApiResponse(
        data=WarehouseData.model_validate(await service.create(context, payload))
    )


@router.get("/{warehouseId}", response_model=ApiResponse[WarehouseData])
async def get_warehouse(
    warehouse_id: Annotated[UUID, Path(alias="warehouseId")],
    context: CurrentAuthContext,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> ApiResponse[WarehouseData]:
    return ApiResponse(
        data=WarehouseData.model_validate(await service.get(context, warehouse_id))
    )


@router.patch("/{warehouseId}", response_model=ApiResponse[WarehouseData])
async def update_warehouse(
    warehouse_id: Annotated[UUID, Path(alias="warehouseId")],
    payload: WarehouseUpdate,
    context: CurrentAuthContext,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> ApiResponse[WarehouseData]:
    return ApiResponse(
        data=WarehouseData.model_validate(
            await service.update(context, warehouse_id, payload)
        )
    )


__all__ = ["get_warehouse_service", "router"]
