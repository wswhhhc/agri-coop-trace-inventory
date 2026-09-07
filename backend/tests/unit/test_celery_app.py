from app.core.config import Settings
from app.tasks.celery_app import TASK_MODULES, create_celery_app


def test_celery_app_includes_all_background_task_modules() -> None:
    settings = Settings(
        _env_file=None,
        postgres_password="unit-test-password",
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
    )

    application = create_celery_app(settings)

    assert tuple(application.conf.include) == TASK_MODULES
