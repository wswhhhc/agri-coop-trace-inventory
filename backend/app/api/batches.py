from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._cache import get_detail_query_cache
from app.api._pagination import build_pagination_meta
from app.api.traceability import get_traceability_cache
from app.core.audit.service import (
    AuditEvent,
    AuditLogService,
    audit_error_code,
    record_audit_safely,
)
from app.core.auth.dependencies import CurrentAuthContext, get_audit_log_service
from app.infrastructure.database import get_db_session
from app.models import Batch
from app.schemas.batch import BatchCreate, BatchData, BatchListParams, BatchUpdate
from app.schemas.common import ApiResponse, ListResponse
from app.services.batch import BatchService
from app.services.query_cache import QueryCache
from app.services.traceability import TraceabilityCache

router = APIRouter(prefix="/batches", tags=["batches"])
logger = logging.getLogger(__name__)


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
    request: Request,
    service: Annotated[BatchService, Depends(get_batch_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[BatchData]:
    try:
        batch = await service.create(context, payload)
    except Exception as error:
        await record_audit_safely(
            audit_log_service,
            AuditEvent(
                action="CREATE_BATCH",
                module="BATCH",
                object_type="BATCH",
                result="FAILURE",
                cooperative_id=context.cooperative_id,
                user_id=context.user_id,
                request_id=getattr(request.state, "request_id", None),
                detail={"errorCode": audit_error_code(error)},
            ),
            logger,
        )
        raise
    await record_audit_safely(
        audit_log_service,
        AuditEvent(
            action="CREATE_BATCH",
            module="BATCH",
            object_type="BATCH",
            result="SUCCESS",
            cooperative_id=batch.cooperative_id,
            user_id=context.user_id,
            object_id=batch.id,
            request_id=getattr(request.state, "request_id", None),
            detail={
                "batchNo": batch.batch_no,
                "productId": str(batch.product_id),
            },
        ),
        logger,
    )
    return ApiResponse(data=_batch_data(batch))


@router.get("/{batchId}", response_model=ApiResponse[BatchData])
async def get_batch(
    batch_id: Annotated[UUID, Path(alias="batchId")],
    context: CurrentAuthContext,
    service: Annotated[BatchService, Depends(get_batch_service)],
    cache: Annotated[QueryCache, Depends(get_detail_query_cache)],
) -> ApiResponse[BatchData]:
    service.ensure_read_access(context)
    key = cache.key("batch-detail", context, {"id": batch_id})

    async def load() -> ApiResponse[BatchData]:
        return ApiResponse(data=_batch_data(await service.get(context, batch_id)))

    response = await cache.get_or_set(key, ApiResponse[BatchData], load)
    return response if response is not None else await load()


@router.patch("/{batchId}", response_model=ApiResponse[BatchData])
async def update_batch(
    batch_id: Annotated[UUID, Path(alias="batchId")],
    payload: BatchUpdate,
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[BatchService, Depends(get_batch_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
    cache: Annotated[QueryCache, Depends(get_detail_query_cache)],
) -> ApiResponse[BatchData]:
    try:
        batch = await service.update(context, batch_id, payload)
    except Exception as error:
        await record_audit_safely(
            audit_log_service,
            AuditEvent(
                action="UPDATE_BATCH",
                module="BATCH",
                object_type="BATCH",
                result="FAILURE",
                cooperative_id=context.cooperative_id,
                user_id=context.user_id,
                object_id=batch_id,
                request_id=getattr(request.state, "request_id", None),
                detail={"errorCode": audit_error_code(error)},
            ),
            logger,
        )
        raise
    await record_audit_safely(
        audit_log_service,
        AuditEvent(
            action="UPDATE_BATCH",
            module="BATCH",
            object_type="BATCH",
            result="SUCCESS",
            cooperative_id=batch.cooperative_id,
            user_id=context.user_id,
            object_id=batch.id,
            request_id=getattr(request.state, "request_id", None),
            detail={
                "updatedFields": sorted(
                    payload.model_dump(exclude_unset=True).keys()
                )
            },
        ),
        logger,
    )
    await cache.invalidate_resource("batch-detail", batch.cooperative_id)
    return ApiResponse(data=_batch_data(batch))


__all__ = ["get_batch_service", "router"]
