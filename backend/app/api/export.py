from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.schemas.alerting import TaskData
from app.schemas.common import ApiResponse
from app.schemas.export import ExportTaskCreate
from app.services.export import ExportService
from app.tasks.export_tasks import generate_export_task

router = APIRouter(tags=["export"])


def get_export_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExportService:
    return ExportService(session)


@router.post("/export-tasks", response_model=ApiResponse[TaskData], status_code=202)
async def submit_export_task(
    payload: ExportTaskCreate,
    context: CurrentAuthContext,
    service: Annotated[ExportService, Depends(get_export_service)],
) -> ApiResponse[TaskData]:
    record = await service.submit(context, payload, generate_export_task.apply_async)
    return ApiResponse(data=TaskData.model_validate(record))


__all__ = ["get_export_service", "router"]
