from __future__ import annotations

from uuid import uuid4

from app.core.config import Settings
from app.schemas.product import ProductListParams
from app.schemas.warehouse import WarehouseListParams
from app.services.reference_cache_policy import is_cacheable_reference_list


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
    )


def test_reference_cache_settings_have_safe_defaults() -> None:
    settings = _settings()

    assert settings.reference_cache_ttl_seconds == 900
    assert settings.cache_ttl_jitter_ratio == 0.1


def test_only_common_reference_list_shape_is_cacheable() -> None:
    assert is_cacheable_reference_list(ProductListParams())
    assert is_cacheable_reference_list(WarehouseListParams(page_size=100))
    assert not is_cacheable_reference_list(ProductListParams(keyword="番茄"))
    assert not is_cacheable_reference_list(ProductListParams(category_id=uuid4()))
    assert not is_cacheable_reference_list(ProductListParams(is_active=True))
    assert not is_cacheable_reference_list(ProductListParams(page=2))
    assert not is_cacheable_reference_list(ProductListParams(sort_by="name"))
