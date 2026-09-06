from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.schemas.dashboard import DashboardQueryParams, ProductRankingParams
from app.services.dashboard_cache import DashboardCache
from app.services.dashboard_policy import (
    require_dashboard_read,
    require_forecast_comparison,
)


class MemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, *, ex: int) -> None:
        self.values[key] = value

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)


def _context(*, role_code: str, permissions: set[str]) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="dashboard-user",
        real_name="大屏用户",
        role_code=role_code,
        permission_codes=frozenset(permissions),
        cooperative_id=uuid4(),
        warehouse_ids=frozenset({uuid4()}),
        session_id="session",
        token_id="token",
    )


def test_dashboard_query_uses_camel_case_and_validates_date_range() -> None:
    params = DashboardQueryParams.model_validate(
        {"warehouseId": uuid4(), "startDate": "2026-09-01", "endDate": "2026-09-30"}
    )

    assert params.warehouse_id is not None
    assert params.start_date == date(2026, 9, 1)
    assert params.end_date == date(2026, 9, 30)

    with pytest.raises(ValueError, match="开始日期不能晚于结束日期"):
        DashboardQueryParams.model_validate(
            {"startDate": "2026-09-30", "endDate": "2026-09-01"}
        )

    with pytest.raises(ValueError, match="查询时间范围不能超过 366 天"):
        DashboardQueryParams.model_validate(
            {"startDate": "2025-01-01", "endDate": "2026-01-02"}
        )


def test_product_ranking_limit_is_bounded() -> None:
    assert ProductRankingParams(limit=10).limit == 10

    with pytest.raises(ValueError):
        ProductRankingParams(limit=101)


def test_dashboard_read_permission_matches_existing_read_roles() -> None:
    require_dashboard_read(
        _context(role_code="WAREHOUSE_STAFF", permissions={"inventory:read"})
    )

    with pytest.raises(AppException) as error:
        require_dashboard_read(
            _context(role_code="WAREHOUSE_STAFF", permissions=set())
        )
    assert error.value.status_code == 403


def test_forecast_comparison_requires_model_read_permission() -> None:
    require_forecast_comparison(
        _context(role_code="COOPERATIVE_ADMIN", permissions={"model:read"})
    )

    with pytest.raises(AppException) as error:
        require_forecast_comparison(
            _context(role_code="WAREHOUSE_STAFF", permissions={"inventory:read"})
        )
    assert error.value.status_code == 403


def test_dashboard_cache_key_is_stable_and_scope_aware() -> None:
    cooperative_id = uuid4()
    warehouse_a, warehouse_b = uuid4(), uuid4()
    cache = DashboardCache(object(), key_prefix="agri:", ttl_seconds=300)

    first = cache.key(
        "summary",
        cooperative_id,
        frozenset({warehouse_a, warehouse_b}),
        {"startDate": "2026-09-01", "endDate": "2026-09-30"},
    )
    second = cache.key(
        "summary",
        cooperative_id,
        frozenset({warehouse_b, warehouse_a}),
        {"endDate": "2026-09-30", "startDate": "2026-09-01"},
    )
    other_scope = cache.key(
        "summary", cooperative_id, frozenset({warehouse_a}), {"startDate": "2026-09-01"}
    )

    assert first == second
    assert first != other_scope
    assert first.startswith("agri:dashboard:summary:")


@pytest.mark.asyncio
async def test_dashboard_cache_round_trips_json_payload() -> None:
    redis = MemoryRedis()
    cache = DashboardCache(redis, key_prefix="agri:", ttl_seconds=300)

    await cache.set("agri:key", {"count": 2, "units": ["KG"]})

    assert await cache.get("agri:key") == {"count": 2, "units": ["KG"]}
