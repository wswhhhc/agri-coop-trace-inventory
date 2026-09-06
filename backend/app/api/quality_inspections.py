from __future__ import annotations

import logging
from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.service import AuditEvent, AuditLogService
from app.core.auth.dependencies import CurrentAuthContext, get_audit_log_service
from app.core.exceptions import AppException
from app.infrastructure.database import get_db_session
from app.models import QualityInspection
from app.schemas.common import ApiResponse, ListResponse, PaginationMeta
from app.schemas.quality_inspection import (
    QualityInspectionCreate,
    QualityInspectionData,
    QualityInspectionItemData,
    QualityInspectionListParams,
)
from app.services.quality_inspection import QualityInspectionService

router = APIRouter(
    prefix="/batches/{batchId}/quality-inspections",
    tags=["quality-inspections"],
)
logger = logging.getLogger(__name__)


def get_quality_inspection_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> QualityInspectionService:
    return QualityInspectionService(session)


def _quality_inspection_data(
    inspection: QualityInspection,
    *,
    fallback_inspector_name: str | None = None,
) -> QualityInspectionData:
    inspector_name = (
        inspection.inspector.real_name
        if inspection.inspector is not None
        else fallback_inspector_name or ""
    )
    return QualityInspectionData(
        id=inspection.id,
        cooperative_id=inspection.cooperative_id,
        batch_id=inspection.batch_id,
        inspection_no=inspection.inspection_no,
        inspection_date=inspection.inspected_at.date(),
        inspector_id=inspection.inspector_id,
        inspector_name=inspector_name,
        conclusion=inspection.conclusion,
        remarks=inspection.remarks,
        original_inspection_id=inspection.original_inspection_id,
        items=[
            QualityInspectionItemData(
                id=item.id,
                name=item.item_name,
                value=item.result_value,
                unit=item.unit,
                standard=item.standard_value,
                is_qualified=item.is_qualified,
                sort_order=item.sort_order,
            )
            for item in inspection.items
        ],
        attachment_file_ids=[link.file_id for link in inspection.file_links],
        created_at=inspection.created_at,
        updated_at=inspection.updated_at,
    )


@router.get("", response_model=ListResponse[QualityInspectionData])
async def list_quality_inspections(
    batch_id: Annotated[UUID, Path(alias="batchId")],
    params: Annotated[QualityInspectionListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[
        QualityInspectionService, Depends(get_quality_inspection_service)
    ],
) -> ListResponse[QualityInspectionData]:
    items, total = await service.list(context, batch_id, params)
    return ListResponse(
        data=[_quality_inspection_data(item) for item in items],
        pagination=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=ceil(total / params.page_size) if total else 0,
        ),
    )


@router.post("", response_model=ApiResponse[QualityInspectionData], status_code=201)
async def create_quality_inspection(
    batch_id: Annotated[UUID, Path(alias="batchId")],
    payload: QualityInspectionCreate,
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[
        QualityInspectionService, Depends(get_quality_inspection_service)
    ],
    audit_log_service: Annotated[
        AuditLogService, Depends(get_audit_log_service)
    ],
) -> ApiResponse[QualityInspectionData]:
    try:
        inspection = await service.create(context, batch_id, payload)
    except AppException as error:
        await _record_audit(
            audit_log_service,
            AuditEvent(
                action="CREATE_QUALITY_INSPECTION",
                module="QUALITY",
                object_type="QUALITY_INSPECTION",
                result="FAILURE",
                cooperative_id=context.cooperative_id,
                user_id=context.user_id,
                request_id=getattr(request.state, "request_id", None),
                detail={"errorCode": error.code},
            ),
        )
        raise
    await _record_audit(
        audit_log_service,
        AuditEvent(
            action="CREATE_QUALITY_INSPECTION",
            module="QUALITY",
            object_type="QUALITY_INSPECTION",
            result="SUCCESS",
            cooperative_id=inspection.cooperative_id,
            user_id=context.user_id,
            object_id=inspection.id,
            request_id=getattr(request.state, "request_id", None),
            detail={
                "conclusion": inspection.conclusion.value,
                "itemCount": len(inspection.items),
            },
        ),
    )
    return ApiResponse(
        data=_quality_inspection_data(
            inspection, fallback_inspector_name=context.real_name
        )
    )


async def _record_audit(audit_service: AuditLogService, event: AuditEvent) -> None:
    try:
        await audit_service.record(event)
    except Exception:
        logger.exception("质检审计记录失败 action=%s", event.action)


__all__ = ["get_quality_inspection_service", "router"]
