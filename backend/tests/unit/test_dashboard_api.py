from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import httpx
import pytest
from app.api.dashboard import get_dashboard_service
from app.core.auth.context import AuthContext
from app.core.auth.dependencies import get_auth_context
from app.main import create_app
from app.schemas.dashboard import (
    AlertDistributionData,
    AlertDistributionResult,
    DashboardSummaryData,
    InventoryTrendData,
    InventoryUnitSummary,
    ProductRankingData,
)


class FakeDashboardService:
    async def summary(self, context, params):
        return DashboardSummaryData(
            product_count=1,
            batch_count=2,
            inventory_by_unit=[InventoryUnitSummary(unit="KG", quantity=10)],
            pending_alert_count=1,
            expiring_batch_count=0,
            low_stock_product_count=0,
            updated_at=datetime.now(UTC),
        )

    async def inventory_trends(self, context, params):
        return (
            [
                InventoryTrendData(
                    date=date(2026, 9, 1),
                    unit="KG",
                    inbound_quantity=10,
                    outbound_quantity=2,
                    ending_quantity=8,
                )
            ],
            11,
        )

    async def alert_distribution(self, context, params):
        return AlertDistributionResult(
            total_count=1,
            items=[AlertDistributionData(alert_type="LOW_STOCK", severity="HIGH", count=1)],
        )

    async def product_ranking(self, context, params):
        return [
            ProductRankingData(
                product_id=uuid4(),
                product_name="番茄",
                unit="KG",
                outbound_quantity=2,
                outbound_count=1,
            )
        ]

    async def forecast_comparison(self, context, params):
        return []


def _context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="dashboard-api",
        real_name="大屏用户",
        role_code="COOPERATIVE_ADMIN",
        permission_codes=frozenset({"inventory:read", "model:read"}),
        cooperative_id=uuid4(),
        warehouse_ids=None,
        session_id="session",
        token_id="token",
    )


@pytest.mark.asyncio
async def test_dashboard_routes_are_registered_and_return_api_data() -> None:
    application = create_app()
    application.dependency_overrides[get_auth_context] = _context
    application.dependency_overrides[get_dashboard_service] = FakeDashboardService

    paths = set(application.openapi()["paths"])
    assert {
        "/api/v1/dashboard/summary",
        "/api/v1/dashboard/inventory-trends",
        "/api/v1/dashboard/alert-distribution",
        "/api/v1/dashboard/product-ranking",
        "/api/v1/dashboard/forecast-comparison",
    } <= paths

    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        summary = await client.get(
            "/api/v1/dashboard/summary",
            params={"startDate": "2026-09-01", "endDate": "2026-09-02"},
        )
        trends = await client.get(
            "/api/v1/dashboard/inventory-trends", params={"page": 2, "pageSize": 10}
        )
        distribution = await client.get("/api/v1/dashboard/alert-distribution")
        ranking = await client.get("/api/v1/dashboard/product-ranking?limit=5")
        comparison = await client.get("/api/v1/dashboard/forecast-comparison")

    assert summary.status_code == 200
    assert summary.json()["data"]["inventoryByUnit"][0]["quantity"] == 10
    assert trends.status_code == 200
    assert trends.json()["data"][0]["endingQuantity"] == 8
    assert trends.json()["pagination"] == {
        "page": 2,
        "pageSize": 10,
        "totalItems": 11,
        "totalPages": 2,
    }
    assert distribution.status_code == 200
    assert distribution.json()["data"]["totalCount"] == 1
    assert ranking.status_code == 200
    assert ranking.json()["data"][0]["productName"] == "番茄"
    assert comparison.status_code == 200
    assert comparison.json()["data"] == []
