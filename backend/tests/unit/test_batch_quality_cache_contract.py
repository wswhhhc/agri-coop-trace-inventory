from __future__ import annotations

from app.core.config import Settings
from app.schemas.quality_inspection import QualityInspectionListParams
from app.services.quality_cache_policy import is_cacheable_quality_list


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
    )


def test_detail_cache_has_short_ttl() -> None:
    assert _settings().detail_cache_ttl_seconds == 180


def test_quality_cache_only_accepts_common_first_page() -> None:
    assert is_cacheable_quality_list(QualityInspectionListParams())
    assert is_cacheable_quality_list(QualityInspectionListParams(page_size=100))
    assert not is_cacheable_quality_list(QualityInspectionListParams(page=2))
    assert not is_cacheable_quality_list(
        QualityInspectionListParams(sort_by="inspectionDate")
    )
