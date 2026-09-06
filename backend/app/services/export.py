from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import resource_not_found
from app.core.auth.context import AuthContext
from app.core.config import Settings
from app.core.exceptions import AppException
from app.infrastructure.transaction import transaction_scope
from app.models import TaskRecord, TaskStatus
from app.repositories.export import ExportRepository
from app.schemas.export import ExportFilters, ExportTaskCreate
from app.services.export_policy import require_export
from app.services.export_storage import safe_export_path
from app.services.task import TaskService


class ExportService:
    """报表导出任务提交和查询数据的业务门面。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ExportRepository(session)

    async def submit(
        self,
        context: AuthContext,
        payload: ExportTaskCreate,
        enqueue: Callable[..., object],
    ) -> TaskRecord:
        require_export(context, payload.report_type)
        assert context.cooperative_id is not None
        await self.validate_filters(context, payload.filters)

        celery_task_id = str(uuid4())
        async with transaction_scope(self.session):
            record = TaskRecord(
                cooperative_id=context.cooperative_id,
                task_type="EXPORT_REPORT",
                celery_task_id=celery_task_id,
                status=TaskStatus.PENDING,
                requested_by=context.user_id,
                request_payload=payload.model_dump(mode="json", by_alias=True),
            )
            self.session.add(record)
            await self.session.flush()
        try:
            enqueue(args=[str(record.id)], kwargs={}, task_id=celery_task_id)
        except Exception as error:
            async with transaction_scope(self.session):
                failed = await self.session.get(TaskRecord, record.id, with_for_update=True)
                if failed is not None:
                    failed.status = TaskStatus.FAILURE
                    failed.error_code = "TASK_SUBMIT_FAILED"
                    failed.error_message = str(error)[:500]
            raise
        return record

    async def validate_filters(
        self, context: AuthContext, filters: ExportFilters
    ) -> tuple[date, date]:
        assert context.cooperative_id is not None
        if filters.warehouse_id is not None:
            if not context.has_warehouse_access(filters.warehouse_id):
                raise resource_not_found()
            async with transaction_scope(self.session):
                if not await self.repository.warehouse_in_cooperative(
                    context.cooperative_id, filters.warehouse_id
                ):
                    raise resource_not_found()
        return resolve_export_dates(filters)

    async def download(
        self, context: AuthContext, task_id: UUID, settings: Settings
    ) -> tuple[Path, str]:
        task = await TaskService(self.session).get(context, task_id)
        if task.task_type != "EXPORT_REPORT" or task.result_payload is None:
            raise AppException(
                code="EXPORT_NOT_READY", message="导出文件尚未生成", status_code=409
            )
        expires_at_raw = task.result_payload.get("expiresAt")
        filename = task.result_payload.get("filename")
        if not isinstance(expires_at_raw, str) or not isinstance(filename, str):
            raise AppException(
                code="EXPORT_RESULT_INVALID", message="导出结果无效", status_code=500
            )
        try:
            expires_at = datetime.fromisoformat(expires_at_raw)
        except ValueError as error:
            raise AppException(
                code="EXPORT_RESULT_INVALID", message="导出结果无效", status_code=500
            ) from error
        if expires_at <= datetime.now(UTC):
            raise AppException(
                code="EXPORT_EXPIRED", message="导出文件已过期", status_code=410
            )
        target = safe_export_path(settings.export_storage_path, filename)
        if not target.is_file():
            raise resource_not_found()
        return target, filename


def resolve_export_dates(
    filters: ExportFilters, *, today: date | None = None
) -> tuple[date, date]:
    end_date = filters.end_date or today or datetime.now(UTC).date()
    start_date = filters.start_date or end_date - timedelta(days=29)
    return start_date, end_date


__all__ = ["ExportService", "resolve_export_dates"]
