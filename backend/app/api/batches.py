from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.api.traceability import get_traceability_cache
from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.models import Batch
from app.schemas.batch import BatchCreate, BatchData, BatchListParams, BatchUpdate
from app.schemas.common import ApiResponse, ListResponse
from app.services.batch import BatchService
from app.services.traceability import TraceabilityCache

router = APIRouter(prefix="/batches", tags=["batches"])


def get_batch_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cache: Annotated[TraceabilityCache, Depends(get_traceability_cache)],
) -> BatchService:
    return BatchService(session, cache)


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
        pagination=build_pagination_meta(total, params.page, params.page_size),
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
