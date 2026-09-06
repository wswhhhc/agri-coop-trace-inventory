from __future__ import annotations

from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import CurrentAuthContext
from app.core.config import Settings, get_settings
from app.infrastructure.database import get_db_session
from app.infrastructure.redis import get_redis_client
from app.models import TraceEvent
from app.schemas.common import ApiResponse, ListResponse, PaginationMeta
from app.schemas.traceability import (
    PublicTraceData,
    TraceEventData,
    TraceEventListParams,
)
from app.services.traceability import (
    PublicTraceabilityService,
    TraceabilityCache,
    TraceabilityService,
)

router = APIRouter(
    prefix="/batches/{batchId}/trace-events",
    tags=["traceability"],
)
public_router = APIRouter(tags=["public-traceability"])


def get_traceability_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TraceabilityService:
    return TraceabilityService(session)


def get_public_traceability_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> PublicTraceabilityService:
    return PublicTraceabilityService(
        session,
        get_traceability_cache(settings, redis),
    )


def get_traceability_cache(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> TraceabilityCache:
    return TraceabilityCache(
        redis,
        key_prefix=settings.redis_key_prefix,
        ttl_seconds=settings.trace_cache_ttl_seconds,
    )


def _trace_event_data(event: TraceEvent) -> TraceEventData:
    return TraceEventData.model_validate(event)


@router.get("", response_model=ListResponse[TraceEventData])
async def list_trace_events(
    batch_id: Annotated[UUID, Path(alias="batchId")],
    params: Annotated[TraceEventListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[TraceabilityService, Depends(get_traceability_service)],
) -> ListResponse[TraceEventData]:
    items, total = await service.list_internal(context, batch_id, params)
    return ListResponse(
        data=[_trace_event_data(item) for item in items],
        pagination=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=ceil(total / params.page_size) if total else 0,
        ),
    )


@public_router.get(
    "/public/traces/{traceCode}",
    response_model=ApiResponse[PublicTraceData],
)
async def get_public_trace(
    trace_code: Annotated[str, Path(alias="traceCode", min_length=1, max_length=64)],
    service: Annotated[
        PublicTraceabilityService, Depends(get_public_traceability_service)
    ],
) -> ApiResponse[PublicTraceData]:
    return ApiResponse(data=await service.get_public(trace_code))


__all__ = [
    "get_public_traceability_service",
    "get_traceability_cache",
    "get_traceability_service",
    "public_router",
    "router",
]
