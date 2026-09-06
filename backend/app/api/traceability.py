from __future__ import annotations

from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.models import TraceEvent
from app.schemas.common import ListResponse, PaginationMeta
from app.schemas.traceability import TraceEventData, TraceEventListParams
from app.services.traceability import TraceabilityService

router = APIRouter(
    prefix="/batches/{batchId}/trace-events",
    tags=["traceability"],
)


def get_traceability_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TraceabilityService:
    return TraceabilityService(session)


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


__all__ = ["get_traceability_service", "router"]
