from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "jwt_secret_key": "unit-test-secret",
        "postgres_password": "unit-test-password",
    }
    values.update(overrides)
    return Settings(**values)


def test_settings_builds_database_url_and_parses_csv_values() -> None:
    settings = _settings(
        cors_allowed_origins="http://localhost:5173,https://example.test",
        allowed_upload_content_types="application/pdf,image/png",
        ml_allowed_horizons_days="7,30",
    )

    assert settings.sqlalchemy_database_url == (
        "postgresql+asyncpg://postgres:unit-test-password@localhost:5432/agri_trace"
    )
    assert settings.cors_origins == [
        "http://localhost:5173",
        "https://example.test",
    ]
    assert settings.upload_content_types == ["application/pdf", "image/png"]
    assert settings.ml_allowed_horizons == [7, 30]


def test_settings_resolves_relative_storage_paths_from_backend_root() -> None:
    settings = _settings(file_storage_dir="storage/uploads")

    assert settings.file_storage_path == (
        Path(__file__).resolve().parents[2] / "storage" / "uploads"
    )


def test_settings_resolves_relative_log_path_from_backend_root() -> None:
    settings = _settings(log_dir="storage/logs")

    assert settings.log_dir_path == (
        Path(__file__).resolve().parents[2] / "storage" / "logs"
    )


def test_settings_requires_database_password_without_database_url() -> None:
    with pytest.raises(ValidationError, match="POSTGRES_PASSWORD"):
        _settings(postgres_password=None, database_url=None)


def test_production_settings_reject_placeholder_secret_and_insecure_cookie() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        _settings(
            app_env="production",
            jwt_secret_key="replace-with-a-random-secret",
            refresh_token_cookie_secure=False,
        )


def test_production_settings_require_secure_refresh_cookie() -> None:
    with pytest.raises(ValidationError, match="REFRESH_TOKEN_COOKIE_SECURE"):
        _settings(app_env="production", refresh_token_cookie_secure=False)
