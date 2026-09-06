from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.schemas.audit_log import AuditLogData, AuditLogListParams
from app.schemas.common import ApiResponse, ListResponse
from app.services.audit_log import AuditLogQueryService, audit_log_data

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def get_audit_log_query_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuditLogQueryService:
    return AuditLogQueryService(session)


@router.get("", response_model=ListResponse[AuditLogData])
async def list_audit_logs(
    params: Annotated[AuditLogListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[AuditLogQueryService, Depends(get_audit_log_query_service)],
) -> ListResponse[AuditLogData]:
    records, total = await service.list(context, params)
    return ListResponse(
        data=[AuditLogData.model_validate(audit_log_data(record)) for record in records],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@router.get("/{auditLogId}", response_model=ApiResponse[AuditLogData])
async def get_audit_log(
    audit_log_id: Annotated[UUID, Path(alias="auditLogId")],
    context: CurrentAuthContext,
    service: Annotated[AuditLogQueryService, Depends(get_audit_log_query_service)],
) -> ApiResponse[AuditLogData]:
    return ApiResponse(
        data=AuditLogData.model_validate(
            audit_log_data(await service.get(context, audit_log_id))
        )
    )


__all__ = ["get_audit_log_query_service", "router"]
