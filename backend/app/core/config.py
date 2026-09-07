from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _parse_list(value: Any, item_type: type = str) -> list[Any]:
    """支持 dotenv 中的逗号分隔值，也兼容 JSON 数组。"""
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        if value.startswith("["):
            value = json.loads(value)
        else:
            value = [item.strip() for item in value.split(",") if item.strip()]
    if not isinstance(value, (list, tuple, set)):
        raise TypeError("配置值必须是逗号分隔字符串或数组")
    return [item_type(item) for item in value]


class DatabaseSettings(BaseSettings):
    """数据库配置子集，供 Alembic 在不加载应用密钥的情况下使用。"""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # PostgreSQL
    database_url: SecretStr | None = None
    postgres_host: str = "localhost"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = "agri_trace"
    postgres_user: str = "postgres"
    postgres_password: SecretStr | None = None
    db_pool_size: int = Field(default=10, ge=1)
    db_max_overflow: int = Field(default=20, ge=0)
    db_pool_timeout_seconds: int = Field(default=30, ge=1)
    db_pool_recycle_seconds: int = Field(default=1800, ge=0)
    db_echo: bool = False

    @field_validator("database_url", "postgres_password", mode="before")
    @classmethod
    def convert_blank_database_secrets_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_database_configuration(self) -> DatabaseSettings:
        if self.database_url is None and self.postgres_password is None:
            raise ValueError("POSTGRES_PASSWORD 或 DATABASE_URL 必须配置")
        return self

    @property
    def sqlalchemy_database_url(self) -> str:
        """返回供 SQLAlchemy 和 Alembic 共用的异步 PostgreSQL DSN。"""
        if self.database_url is not None:
            return self.database_url.get_secret_value()
        assert self.postgres_password is not None
        return URL.create(
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)


class DemoSettings(BaseSettings):
    """演示数据脚本配置，不要求数据库或应用密钥。"""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    demo_data_seed: int = 20260904
    demo_password: SecretStr | None = None

    @field_validator("demo_password", mode="before")
    @classmethod
    def convert_blank_demo_password_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class Settings(DatabaseSettings):
    """应用、基础设施和安全配置。"""

    # 应用
    app_name: str = "agri-coop-trace-inventory"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    api_v1_prefix: str = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_dir: str = "storage/logs"
    log_backup_count: int = Field(default=30, ge=0)
    timezone: str = "Asia/Shanghai"
    docs_enabled: bool = True

    # Redis 与 Celery
    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")
    redis_key_prefix: str = "agri_trace:"
    redis_socket_timeout_seconds: int = Field(default=5, ge=1)
    redis_max_connections: int = Field(default=50, ge=1)
    celery_broker_url: SecretStr = SecretStr("redis://localhost:6379/1")
    celery_result_backend: SecretStr = SecretStr("redis://localhost:6379/2")
    celery_task_always_eager: bool = False
    celery_task_max_retries: int = Field(default=3, ge=0)
    celery_task_retry_backoff_seconds: int = Field(default=60, ge=1)
    celery_task_time_limit_seconds: int = Field(default=900, ge=1)
    celery_result_expires_seconds: int = Field(default=86400, ge=1)
    alert_scan_interval_minutes: int = Field(default=5, ge=1)

    # JWT、刷新会话与 Cookie
    jwt_secret_key: SecretStr = SecretStr("")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    access_token_expire_minutes: int = Field(default=30, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)
    refresh_token_cookie_name: str = "refresh_token"
    refresh_token_cookie_secure: bool = False
    refresh_token_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    refresh_token_cookie_domain: str | None = None
    refresh_token_cookie_path: str = "/api/v1/auth"

    # Web/API
    cors_allowed_origins: str = "http://localhost:5173"
    cors_allow_credentials: bool = True
    cors_allowed_methods: str = "*"
    cors_allowed_headers: str = "*"
    cors_expose_headers: str = "X-Request-ID,Retry-After"
    trusted_hosts: str = ""
    default_page_size: int = Field(default=20, ge=1)
    max_page_size: int = Field(default=100, ge=1)
    idempotency_retention_days: int = Field(default=7, ge=1)

    # 缓存与限流
    trace_cache_ttl_seconds: int = Field(default=600, ge=1)
    public_trace_url: str = Field(default="http://localhost:5173/trace", min_length=1)
    dashboard_cache_ttl_seconds: int = Field(default=300, ge=1)
    permission_cache_ttl_seconds: int = Field(default=300, ge=1)
    reference_cache_ttl_seconds: int = Field(default=900, ge=1)
    forecasting_cache_ttl_seconds: int = Field(default=600, ge=1)
    cache_ttl_jitter_ratio: float = Field(default=0.1, ge=0, le=1)
    login_rate_limit_per_minute: int = Field(default=10, ge=1)
    public_trace_rate_limit_per_minute: int = Field(default=60, ge=1)
    public_qr_rate_limit_per_minute: int = Field(default=120, ge=1)
    ai_task_rate_limit_per_minute: int = Field(default=5, ge=1)

    # 文件存储
    file_storage_backend: Literal["local", "s3"] = "local"
    file_storage_dir: str = "storage/uploads"
    export_storage_dir: str = "storage/exports"
    export_download_ttl_seconds: int = Field(default=900, ge=60)
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    allowed_upload_content_types: str = "application/pdf,image/png,image/jpeg"
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: SecretStr | None = None
    s3_region: str | None = None

    # AI 与演示数据
    model_artifact_dir: str = "storage/models"
    ml_default_model_type: Literal["MOVING_AVERAGE", "XGBOOST"] = "XGBOOST"
    ml_random_seed: int = 20260904
    ml_allowed_horizons_days: str = "7,30"
    demo_password: SecretStr | None = None
    demo_data_seed: int = 20260904

    @field_validator("jwt_secret_key", mode="before")
    @classmethod
    def convert_blank_secrets_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_configuration(self) -> Settings:
        errors: list[str] = []
        if self.database_url is None and self.postgres_password is None:
            errors.append("POSTGRES_PASSWORD 或 DATABASE_URL 必须配置")
        jwt_secret = self.jwt_secret_key.get_secret_value()
        if jwt_secret == "":
            errors.append("JWT_SECRET_KEY 必须配置")
        elif len(jwt_secret.encode("utf-8")) < 32:
            errors.append("JWT_SECRET_KEY 长度至少为 32 字节")
        if self.jwt_issuer is None or not self.jwt_issuer.strip():
            errors.append("JWT_ISSUER 必须配置")
        if self.jwt_audience is None or not self.jwt_audience.strip():
            errors.append("JWT_AUDIENCE 必须配置")
        if self.default_page_size > self.max_page_size:
            errors.append("DEFAULT_PAGE_SIZE 不能大于 MAX_PAGE_SIZE")
        if not self.ml_allowed_horizons:
            errors.append("ML_ALLOWED_HORIZONS_DAYS 不能为空")
        if any(days not in {7, 30} for days in self.ml_allowed_horizons):
            errors.append("ML_ALLOWED_HORIZONS_DAYS 只允许 7 或 30")
        if self.refresh_token_cookie_samesite == "none" and not self.refresh_token_cookie_secure:
            errors.append("SameSite=None 时必须启用 REFRESH_TOKEN_COOKIE_SECURE")
        if self.file_storage_backend == "s3":
            required_s3 = {
                "S3_BUCKET": self.s3_bucket,
                "S3_ACCESS_KEY_ID": self.s3_access_key_id,
                "S3_SECRET_ACCESS_KEY": self.s3_secret_access_key,
            }
            errors.extend(f"{name} 必须配置" for name, value in required_s3.items() if value is None)
        if self.app_env == "production":
            if self.debug:
                errors.append("生产环境必须关闭 DEBUG")
            if self.jwt_secret_key.get_secret_value() == "replace-with-a-random-secret":
                errors.append("生产环境不能使用示例 JWT_SECRET_KEY")
            if not self.refresh_token_cookie_secure:
                errors.append("生产环境必须启用 REFRESH_TOKEN_COOKIE_SECURE")
            if "*" in self.cors_origins:
                errors.append("生产环境 CORS_ALLOWED_ORIGINS 不能使用 *")
        if errors:
            raise ValueError("；".join(errors))
        return self

    @property
    def cors_origins(self) -> list[str]:
        return _parse_list(self.cors_allowed_origins, str)

    @property
    def cors_methods(self) -> list[str]:
        return _parse_list(self.cors_allowed_methods, str)

    @property
    def cors_headers(self) -> list[str]:
        return _parse_list(self.cors_allowed_headers, str)

    @property
    def cors_exposed_headers(self) -> list[str]:
        return _parse_list(self.cors_expose_headers, str)

    @property
    def trusted_host_list(self) -> list[str]:
        return _parse_list(self.trusted_hosts, str)

    @property
    def upload_content_types(self) -> list[str]:
        return _parse_list(self.allowed_upload_content_types, str)

    @property
    def ml_allowed_horizons(self) -> list[int]:
        return _parse_list(self.ml_allowed_horizons_days, int)

    @property
    def file_storage_path(self) -> Path:
        path = Path(self.file_storage_dir)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def export_storage_path(self) -> Path:
        path = Path(self.export_storage_dir)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def model_artifact_path(self) -> Path:
        path = Path(self.model_artifact_dir)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def log_dir_path(self) -> Path:
        path = Path(self.log_dir)
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取进程内唯一配置实例。"""
    return Settings()


__all__ = [
    "PROJECT_ROOT",
    "DatabaseSettings",
    "DemoSettings",
    "Settings",
    "get_settings",
]
