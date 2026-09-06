from datetime import timedelta
from uuid import uuid4

from app.core.auth.context import AuthContext
from app.core.config import Settings
from app.services.inventory import InventoryService
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


def test_inventory_mutation_schedules_alert_scan_after_success() -> None:
    scheduled = []
    service = InventoryService.__new__(InventoryService)
    service.alert_scheduler = lambda **kwargs: scheduled.append(kwargs)
    context = AuthContext(
        user_id=uuid4(), username="u", real_name="用户", role_code="COOPERATIVE_ADMIN",
        permission_codes=frozenset(), cooperative_id=uuid4(), warehouse_ids=None,
        session_id="s", token_id="t",
    )
    service._schedule_alert_scan(context)
    assert scheduled == [{"args": [str(context.cooperative_id)], "kwargs": {}}]
