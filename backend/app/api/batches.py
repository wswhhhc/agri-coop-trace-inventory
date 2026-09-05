from __future__ import annotations

from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.models import Batch
from app.schemas.batch import BatchCreate, BatchData, BatchListParams, BatchUpdate
from app.schemas.common import ApiResponse, ListResponse, PaginationMeta
from app.services.batch import BatchService

router = APIRouter(prefix="/batches", tags=["batches"])


def get_batch_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> BatchService:
    return BatchService(session)


def _batch_data(batch: Batch) -> BatchData:
    return BatchData.model_validate(batch)


@router.get("", response_model=ListResponse[BatchData])
async def list_batches(
    params: Annotated[BatchListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[BatchService, Depends(get_batch_service)],
) -> ListResponse[BatchData]:
    items, total = await service.list(context, params)
    return ListResponse(
        data=[_batch_data(item) for item in items],
        pagination=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=ceil(total / params.page_size) if total else 0,
        ),
    )


@router.post("", response_model=ApiResponse[BatchData], status_code=201)
async def create_batch(
    payload: BatchCreate,
    context: CurrentAuthContext,
    service: Annotated[BatchService, Depends(get_batch_service)],
) -> ApiResponse[BatchData]:
    return ApiResponse(data=_batch_data(await service.create(context, payload)))


@router.get("/{batchId}", response_model=ApiResponse[BatchData])
async def get_batch(
    batch_id: Annotated[UUID, Path(alias="batchId")],
    context: CurrentAuthContext,
    service: Annotated[BatchService, Depends(get_batch_service)],
) -> ApiResponse[BatchData]:
    return ApiResponse(data=_batch_data(await service.get(context, batch_id)))


@router.patch("/{batchId}", response_model=ApiResponse[BatchData])
async def update_batch(
    batch_id: Annotated[UUID, Path(alias="batchId")],
    payload: BatchUpdate,
    context: CurrentAuthContext,
    service: Annotated[BatchService, Depends(get_batch_service)],
) -> ApiResponse[BatchData]:
    return ApiResponse(
        data=_batch_data(await service.update(context, batch_id, payload))
    )


__all__ = ["get_batch_service", "router"]
