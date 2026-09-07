from __future__ import annotations

from uuid import uuid4

from app.core.config import Settings
from app.schemas.forecasting import ModelVersionListParams
from app.services.forecasting_cache_policy import is_cacheable_active_model_list


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
    )


def test_forecasting_cache_has_short_rebuild_ttl() -> None:
    assert _settings().forecasting_cache_ttl_seconds == 600


def test_only_active_model_version_list_is_cacheable() -> None:
    assert is_cacheable_active_model_list(
        ModelVersionListParams(is_active=True)
    )
    assert not is_cacheable_active_model_list(ModelVersionListParams())
    assert not is_cacheable_active_model_list(
        ModelVersionListParams(is_active=True, product_id=uuid4())
    )
    assert not is_cacheable_active_model_list(
        ModelVersionListParams(is_active=True, page=2)
    )
