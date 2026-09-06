from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.context import AuthContext
from app.infrastructure.transaction import transaction_scope
from app.repositories.dashboard import DashboardRepository
from app.schemas.common import BaseSchema
from app.schemas.dashboard import (
    AlertDistributionData,
    AlertDistributionResult,
    DashboardQueryParams,
    DashboardSummaryData,
    ForecastComparisonData,
    InventoryTrendData,
    InventoryUnitSummary,
    ProductRankingData,
    ProductRankingParams,
)
from app.services.dashboard_cache import DashboardCache
from app.services.dashboard_policy import (
    ensure_dashboard_warehouse_scope,
    require_dashboard_read,
    require_forecast_comparison,
    warehouse_ids_for_dashboard,
)


class DashboardService:
    """大屏只读业务门面，聚合结果不改变领域数据。"""

    def __init__(
        self, session: AsyncSession, cache: DashboardCache | None = None
    ) -> None:
        self.session = session
        self.cache = cache
        self.repository = DashboardRepository(session)

    async def summary(
        self, context: AuthContext, params: DashboardQueryParams
    ) -> DashboardSummaryData:
        require_dashboard_read(context)
        ensure_dashboard_warehouse_scope(context, params.warehouse_id)
        cache_key = self._cache_key("summary", context, params)
        if (cached := await self._cache_get(cache_key, DashboardSummaryData)) is not None:
            return cached
        async with transaction_scope(self.session):
            raw = await self.repository.get_summary(
                context.cooperative_id,
                self._warehouse_scope(context, params.warehouse_id),
                today=datetime.now(UTC).date(),
            )
        result = DashboardSummaryData(
            product_count=raw["product_count"],
            batch_count=raw["batch_count"],
            inventory_by_unit=[
                InventoryUnitSummary(unit=row[0], quantity=float(row[1]))
                for row in raw["inventory_by_unit"]
            ],
            pending_alert_count=raw["pending_alert_count"],
            expiring_batch_count=raw["expiring_batch_count"],
            low_stock_product_count=raw["low_stock_product_count"],
            updated_at=datetime.now(UTC),
        )
        await self._cache_set(cache_key, result)
        return result

    async def inventory_trends(
        self, context: AuthContext, params: DashboardQueryParams
    ) -> list[InventoryTrendData]:
        require_dashboard_read(context)
        ensure_dashboard_warehouse_scope(context, params.warehouse_id)
        start_date, end_date = resolve_dashboard_dates(params)
        cache_key = self._cache_key("inventory-trends", context, params)
        if (cached := await self._cache_get(cache_key, InventoryTrendData, many=True)) is not None:
            return cached
        async with transaction_scope(self.session):
            rows = await self.repository.inventory_trends(
                context.cooperative_id,
                self._warehouse_scope(context, params.warehouse_id),
                start_date=start_date,
                end_date=end_date,
            )
        result = [
            InventoryTrendData(
                date=row[0],
                unit=row[1],
                inbound_quantity=float(row[2]),
                outbound_quantity=float(row[3]),
                ending_quantity=float(row[4]),
            )
            for row in rows
        ]
        await self._cache_set(cache_key, result)
        return result

    async def alert_distribution(
        self, context: AuthContext, params: DashboardQueryParams
    ) -> AlertDistributionResult:
        require_dashboard_read(context)
        ensure_dashboard_warehouse_scope(context, params.warehouse_id)
        start_date, end_date = resolve_dashboard_dates(params)
        cache_key = self._cache_key("alert-distribution", context, params)
        if (cached := await self._cache_get(cache_key, AlertDistributionResult)) is not None:
            return cached
        async with transaction_scope(self.session):
            rows = await self.repository.alert_distribution(
                context.cooperative_id,
                self._warehouse_scope(context, params.warehouse_id),
                start_date=start_date,
                end_date=end_date,
            )
        items = [
            AlertDistributionData(alert_type=row[0], severity=row[1], count=row[2])
            for row in rows
        ]
        result = AlertDistributionResult(
            total_count=sum(item.count for item in items), items=items
        )
        await self._cache_set(cache_key, result)
        return result

    async def product_ranking(
        self, context: AuthContext, params: ProductRankingParams
    ) -> list[ProductRankingData]:
        require_dashboard_read(context)
        ensure_dashboard_warehouse_scope(context, params.warehouse_id)
        start_date, end_date = resolve_dashboard_dates(params)
        cache_key = self._cache_key("product-ranking", context, params)
        if (cached := await self._cache_get(cache_key, ProductRankingData, many=True)) is not None:
            return cached
        async with transaction_scope(self.session):
            rows = await self.repository.product_ranking(
                context.cooperative_id,
                self._warehouse_scope(context, params.warehouse_id),
                start_date=start_date,
                end_date=end_date,
                limit=params.limit,
            )
        result = [
            ProductRankingData(
                product_id=row[0],
                product_name=row[1],
                unit=row[2],
                outbound_quantity=float(row[3]),
                outbound_count=row[4],
            )
            for row in rows
        ]
        await self._cache_set(cache_key, result)
        return result

    async def forecast_comparison(
        self, context: AuthContext, params: DashboardQueryParams
    ) -> list[ForecastComparisonData]:
        require_forecast_comparison(context)
        ensure_dashboard_warehouse_scope(context, params.warehouse_id)
        start_date, end_date = resolve_dashboard_dates(params)
        cache_key = self._cache_key("forecast-comparison", context, params)
        if (cached := await self._cache_get(cache_key, ForecastComparisonData, many=True)) is not None:
            return cached
        async with transaction_scope(self.session):
            rows = await self.repository.forecast_comparison(
                context.cooperative_id,
                self._warehouse_scope(context, params.warehouse_id),
                start_date=start_date,
                end_date=end_date,
            )
        result: list[ForecastComparisonData] = []
        for row in rows:
            predicted_demand = float(row[7])
            actual_demand = float(row[8])
            result.append(
                ForecastComparisonData(
                    forecast_result_id=row[0],
                    warehouse_id=row[1],
                    product_id=row[2],
                    model_version_id=row[3],
                    model_version=row[4],
                    forecast_start_date=row[5],
                    forecast_end_date=row[6],
                    predicted_demand=predicted_demand,
                    actual_demand=actual_demand,
                    absolute_error=abs(predicted_demand - actual_demand),
                    metrics=cast(dict[str, float], row[9]),
                )
            )
        await self._cache_set(cache_key, result)
        return result

    def _cache_key(
        self, endpoint: str, context: AuthContext, params: DashboardQueryParams
    ) -> str | None:
        if self.cache is None:
            return None
        start_date, end_date = resolve_dashboard_dates(params)
        filters: dict[str, Any] = {
            "warehouseId": str(params.warehouse_id) if params.warehouse_id else None,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }
        if isinstance(params, ProductRankingParams):
            filters["limit"] = params.limit
        return self.cache.key(
            endpoint,
            context.cooperative_id,
            self._warehouse_scope(context, params.warehouse_id),
            filters,
        )

    async def _cache_get(
        self, key: str | None, model_type: type[BaseSchema], *, many: bool = False
    ) -> Any | None:
        if self.cache is None or key is None:
            return None
        raw = await self.cache.get(key)
        if many:
            return [model_type.model_validate(item) for item in raw] if isinstance(raw, list) else None
        return model_type.model_validate(raw) if isinstance(raw, dict) else None

    async def _cache_set(
        self, key: str | None, value: BaseSchema | Sequence[BaseSchema]
    ) -> None:
        if self.cache is None or key is None:
            return
        payload = (
            value.model_dump(mode="json")
            if isinstance(value, BaseSchema)
            else [item.model_dump(mode="json") for item in value]
        )
        await self.cache.set(key, payload)

    @staticmethod
    def _warehouse_scope(
        context: AuthContext, warehouse_id: UUID | None
    ) -> frozenset[UUID] | None:
        if warehouse_id is not None:
            return frozenset({warehouse_id})
        return warehouse_ids_for_dashboard(context)


def resolve_dashboard_dates(
    params: DashboardQueryParams, *, today: date | None = None
) -> tuple[date, date]:
    end_date = params.end_date or today or datetime.now(UTC).date()
    start_date = params.start_date or end_date - timedelta(days=29)
    return start_date, end_date


__all__ = ["DashboardService", "resolve_dashboard_dates"]
