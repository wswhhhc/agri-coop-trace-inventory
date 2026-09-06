from __future__ import annotations

from io import BytesIO
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

import qrcode  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, Path, Query, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api._pagination import build_pagination_meta
from app.core.auth.dependencies import CurrentAuthContext
from app.core.auth.public_rate_limit import (
    PublicRateLimiter,
    PublicRateLimiterDependencyError,
    PublicRateLimitExceeded,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.infrastructure.database import get_db_session
from app.infrastructure.redis import get_redis_client
from app.models import TraceEvent
from app.schemas.common import ApiResponse, ListResponse
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


def get_public_trace_rate_limiter(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> PublicRateLimiter:
    return PublicRateLimiter(
        redis,
        key_prefix=settings.redis_key_prefix,
        resource="trace",
        max_requests=settings.public_trace_rate_limit_per_minute,
    )


def get_public_qr_rate_limiter(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> PublicRateLimiter:
    return PublicRateLimiter(
        redis,
        key_prefix=settings.redis_key_prefix,
        resource="qr",
        max_requests=settings.public_qr_rate_limit_per_minute,
    )


def build_public_trace_url(settings: Settings, trace_code: str) -> str:
    return f"{settings.public_trace_url.rstrip('/')}/{quote(trace_code, safe='')}"


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
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@public_router.get(
    "/public/traces/{traceCode}",
    response_model=ApiResponse[PublicTraceData],
)
async def get_public_trace(
    trace_code: Annotated[str, Path(alias="traceCode", min_length=1, max_length=64)],
    request: Request,
    limiter: Annotated[
        PublicRateLimiter, Depends(get_public_trace_rate_limiter)
    ],
    service: Annotated[
        PublicTraceabilityService, Depends(get_public_traceability_service)
    ],
) -> ApiResponse[PublicTraceData]:
    await _check_public_rate_limit(limiter, request)
    return ApiResponse(data=await service.get_public(trace_code))


@public_router.get(
    "/public/qr-codes/{traceCode}.png",
    response_class=StreamingResponse,
    responses={404: {"description": "追溯码不存在"}, 429: {"description": "请求过于频繁"}},
)
async def get_public_qr_code(
    trace_code: Annotated[str, Path(alias="traceCode", min_length=1, max_length=64)],
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[PublicRateLimiter, Depends(get_public_qr_rate_limiter)],
    service: Annotated[
        PublicTraceabilityService, Depends(get_public_traceability_service)
    ],
) -> StreamingResponse:
    await _check_public_rate_limit(limiter, request)
    await service.get_public(trace_code)
    target_url = build_public_trace_url(settings, trace_code)
    image = qrcode.make(target_url)
    stream = BytesIO()
    image.save(stream, format="PNG")
    stream.seek(0)
    return StreamingResponse(stream, media_type="image/png")


async def _check_public_rate_limit(
    limiter: PublicRateLimiter, request: Request
) -> None:
    client_ip = request.client.host if request.client is not None else "unknown"
    try:
        await limiter.ensure_allowed(client_ip)
    except PublicRateLimitExceeded as exc:
        raise AppException(
            code="RATE_LIMIT_EXCEEDED",
            message="请求过于频繁",
            status_code=429,
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    except PublicRateLimiterDependencyError as exc:
        raise AppException(
            code="DEPENDENCY_UNAVAILABLE",
            message="公开接口保护依赖暂时不可用",
            status_code=503,
        ) from exc


__all__ = [
    "build_public_trace_url",
    "get_public_qr_rate_limiter",
    "get_public_trace_rate_limiter",
    "get_public_traceability_service",
    "get_traceability_cache",
    "get_traceability_service",
    "public_router",
    "router",
]
