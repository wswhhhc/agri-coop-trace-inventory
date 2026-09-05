import logging

from app.core.config import Settings
from app.core.logging_config import configure_logging


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "jwt_secret_key": "unit-test-secret-with-at-least-32-bytes",
        "jwt_issuer": "agri-api",
        "jwt_audience": "agri-web",
        "postgres_password": "unit-test-password",
    }
    values.update(overrides)
    return Settings(**values)


def _remove_managed_handlers() -> None:
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if getattr(handler, "_agri_managed", False):
            root_logger.removeHandler(handler)
            handler.close()


def test_configure_logging_creates_utf8_file_and_writes_messages(tmp_path) -> None:
    settings = _settings(log_dir=str(tmp_path / "logs"))

    try:
        configure_logging(settings)
        log_file = tmp_path / "logs" / "app.log"
        assert log_file.exists()

        logger = logging.getLogger("tests.logging_config")
        logger.info("库存预警任务已完成")

        for handler in logging.getLogger().handlers:
            handler.flush()

        assert log_file.exists()
        assert "库存预警任务已完成" in log_file.read_text(encoding="utf-8")
    finally:
        _remove_managed_handlers()


def test_configure_logging_is_idempotent(tmp_path) -> None:
    settings = _settings(log_dir=str(tmp_path / "logs"))

    try:
        configure_logging(settings)
        configure_logging(settings)

        managed_handlers = [
            handler
            for handler in logging.getLogger().handlers
            if getattr(handler, "_agri_managed", False)
        ]
        assert len(managed_handlers) == 2
    finally:
        _remove_managed_handlers()
