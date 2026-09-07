from __future__ import annotations

from datetime import timedelta

from celery import Celery  # type: ignore[import-untyped]

from app.core.config import Settings, get_settings

TASK_MODULES = (
    "app.tasks.alerting_tasks",
    "app.tasks.export_tasks",
    "app.tasks.forecasting_tasks",
)


def create_celery_app(settings: Settings | None = None) -> Celery:
    settings = settings or get_settings()
    application = Celery(
        settings.app_name,
        broker=settings.celery_broker_url.get_secret_value(),
        backend=settings.celery_result_backend.get_secret_value(),
        include=TASK_MODULES,
    )
    application.conf.update(
        task_always_eager=settings.celery_task_always_eager,
        task_time_limit=settings.celery_task_time_limit_seconds,
        result_expires=settings.celery_result_expires_seconds,
        task_acks_late=True,
        task_track_started=True,
        beat_schedule={
            "alert-scan": {
                "task": "app.tasks.alerting_tasks.scan_alerts_task",
                "schedule": timedelta(minutes=settings.alert_scan_interval_minutes),
            }
        },
    )
    return application


celery_app = create_celery_app()


__all__ = ["TASK_MODULES", "celery_app", "create_celery_app"]
