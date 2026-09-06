from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from app.core.config import get_settings
from app.infrastructure.database import create_database_engine, create_session_factory
from app.models import TaskRecord, TaskStatus
from app.services.alerting import AlertingService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.alerting_tasks.scan_alerts_task",
    acks_late=True,
    track_started=True,
)
def scan_alerts_task(
    self,
    cooperative_id: str | None = None,
    task_record_id: str | None = None,
) -> dict[str, int]:
    """Celery 同步入口；实际扫描在异步 Session 中完成。"""
    return asyncio.run(_run_scan(cooperative_id, task_record_id, self.request.id))


async def _run_scan(
    cooperative_id: str | None,
    task_record_id: str | None,
    celery_task_id: str,
) -> dict[str, int]:
    settings = get_settings()
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)
    record_uuid = UUID(task_record_id) if task_record_id else None
    try:
        async with session_factory() as session:
            if record_uuid is not None:
                async with session.begin():
                    record = await session.get(TaskRecord, record_uuid, with_for_update=True)
                    if record is not None:
                        record.status = TaskStatus.RUNNING
                        record.started_at = datetime.now(UTC)
                        record.progress = 10
            async with session_factory() as scan_session:
                count = await AlertingService(scan_session).scan(
                    UUID(cooperative_id) if cooperative_id else None
                )
            if record_uuid is not None:
                async with session.begin():
                    record = await session.get(TaskRecord, record_uuid, with_for_update=True)
                    if record is not None:
                        record.status = TaskStatus.SUCCESS
                        record.progress = 100
                        record.finished_at = datetime.now(UTC)
                        record.result_payload = {"createdCount": count}
            return {"createdCount": count}
    except Exception as error:
        logger.exception("预警扫描任务失败 celery_task_id=%s", celery_task_id)
        if record_uuid is not None:
            async with session_factory() as session, session.begin():
                record = await session.get(TaskRecord, record_uuid, with_for_update=True)
                if record is not None:
                    record.status = TaskStatus.FAILURE
                    record.finished_at = datetime.now(UTC)
                    record.error_code = "ALERT_SCAN_FAILED"
                    record.error_message = str(error)[:500]
        raise
    finally:
        await engine.dispose()


__all__ = ["scan_alerts_task"]
