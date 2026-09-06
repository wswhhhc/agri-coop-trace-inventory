from datetime import timedelta

from app.core.config import Settings
from app.tasks.alerting_tasks import scan_alerts_task
from app.tasks.celery_app import create_celery_app


def test_celery_app_configures_periodic_alert_scan_without_connecting() -> None:
    settings = Settings(
        _env_file=None,
        postgres_password="unit-test-password",
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        alert_scan_interval_minutes=7,
        celery_task_always_eager=True,
    )
    application = create_celery_app(settings)
    assert application.conf.task_always_eager is True
    assert application.conf.beat_schedule["alert-scan"]["schedule"] == timedelta(minutes=7)


def test_alert_scan_task_has_stable_name() -> None:
    assert scan_alerts_task.name == "app.tasks.alerting_tasks.scan_alerts_task"
