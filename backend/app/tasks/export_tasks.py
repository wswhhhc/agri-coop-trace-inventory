"""报表导出 Celery 任务。"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from celery import Task  # type: ignore[import-untyped]

from app.core.config import get_settings
from app.infrastructure.database import create_database_engine, create_session_factory
from app.infrastructure.transaction import transaction_scope
from app.models import TaskRecord, TaskStatus
from app.repositories.export import ExportRepository
from app.schemas.export import ExportTaskCreate, ReportType
from app.services.export import resolve_export_dates
from app.services.export_storage import safe_export_path
from app.services.export_workbook import build_alert_workbook, build_inventory_workbook
from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.tasks.export_tasks.generate_export_task",
    acks_late=True,
    track_started=True,
)
def generate_export_task(self: Task, task_record_id: str) -> dict[str, str]:
    return asyncio.run(_run_export(UUID(task_record_id), self.request.id))


async def _run_export(task_id: UUID, celery_task_id: str) -> dict[str, str]:
    settings = get_settings()
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    target: Path | None = None
    try:
        async with factory() as session, transaction_scope(session):
            record = await session.get(TaskRecord, task_id, with_for_update=True)
            if record is None:
                raise ValueError("导出任务不存在")
            if record.cooperative_id is None:
                raise ValueError("导出任务缺少合作社范围")
            record.status = TaskStatus.RUNNING
            record.progress = 10
            record.started_at = datetime.now(UTC)
            await session.flush()

            payload = ExportTaskCreate.model_validate(record.request_payload)
            start_date, end_date = resolve_export_dates(payload.filters)
            repository = ExportRepository(session)
            if payload.report_type is ReportType.INVENTORY_DETAIL:
                rows = await repository.list_inventory_rows(
                    record.cooperative_id,
                    payload.filters.warehouse_id,
                    start_date=start_date,
                    end_date=end_date,
                )
            else:
                rows = await repository.list_alert_rows(
                    record.cooperative_id,
                    payload.filters.warehouse_id,
                    start_date=start_date,
                    end_date=end_date,
                )

            settings.export_storage_path.mkdir(parents=True, exist_ok=True)
            filename = f"{payload.report_type.value.lower()}_{task_id}.xlsx"
            target = safe_export_path(settings.export_storage_path, filename)
            with target.open("wb") as output:
                if payload.report_type is ReportType.INVENTORY_DETAIL:
                    build_inventory_workbook(rows, output)
                else:
                    build_alert_workbook(rows, output)
            expires_at = datetime.now(UTC) + timedelta(
                seconds=settings.export_download_ttl_seconds
            )
            result = {
                "downloadUrl": f"/api/v1/export-files/{task_id}",
                "expiresAt": expires_at.isoformat(),
                "filename": filename,
            }
            record.status = TaskStatus.SUCCESS
            record.progress = 100
            record.result_payload = result
            record.finished_at = datetime.now(UTC)
            await session.flush()
            return result
    except Exception as error:
        if target is not None:
            target.unlink(missing_ok=True)
        async with factory() as session, transaction_scope(session):
            record = await session.get(TaskRecord, task_id, with_for_update=True)
            if record is not None:
                record.status = TaskStatus.FAILURE
                record.error_code = "EXPORT_FAILED"
                record.error_message = str(error)[:500]
                record.started_at = record.started_at or datetime.now(UTC)
                record.finished_at = datetime.now(UTC)
                await session.flush()
        raise
    finally:
        await engine.dispose()
__all__ = ["generate_export_task"]
