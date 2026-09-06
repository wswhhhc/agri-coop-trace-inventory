from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.schemas.common import ApiResponse, ListResponse
from app.schemas.cooperative import (
    CooperativeCreate,
    CooperativeData,
    CooperativeListParams,
    CooperativeUpdate,
)
from app.services.cooperative import CooperativeService

router = APIRouter(prefix="/cooperatives", tags=["cooperatives"])


def get_cooperative_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CooperativeService:
    return CooperativeService(session)


@router.get("", response_model=ListResponse[CooperativeData])
async def list_cooperatives(
    params: Annotated[CooperativeListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[CooperativeService, Depends(get_cooperative_service)],
) -> ListResponse[CooperativeData]:
    items, total = await service.list(context, params)
    return ListResponse(
        data=[CooperativeData.model_validate(item) for item in items],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@router.post("", response_model=ApiResponse[CooperativeData], status_code=201)
async def create_cooperative(
    payload: CooperativeCreate,
    context: CurrentAuthContext,
    service: Annotated[CooperativeService, Depends(get_cooperative_service)],
) -> ApiResponse[CooperativeData]:
    return ApiResponse(
        data=CooperativeData.model_validate(await service.create(context, payload))
    )


@router.get("/{cooperativeId}", response_model=ApiResponse[CooperativeData])
async def get_cooperative(
    cooperative_id: Annotated[UUID, Path(alias="cooperativeId")],
    context: CurrentAuthContext,
    service: Annotated[CooperativeService, Depends(get_cooperative_service)],
) -> ApiResponse[CooperativeData]:
    return ApiResponse(
        data=CooperativeData.model_validate(
            await service.get(context, cooperative_id)
        )
    )


@router.patch("/{cooperativeId}", response_model=ApiResponse[CooperativeData])
async def update_cooperative(
    cooperative_id: Annotated[UUID, Path(alias="cooperativeId")],
    payload: CooperativeUpdate,
    context: CurrentAuthContext,
    service: Annotated[CooperativeService, Depends(get_cooperative_service)],
) -> ApiResponse[CooperativeData]:
    return ApiResponse(
        data=CooperativeData.model_validate(
            await service.update(context, cooperative_id, payload)
        )
    )


__all__ = ["get_cooperative_service", "router"]
