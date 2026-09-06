from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.context import AuthContext
from app.infrastructure.transaction import transaction_scope
from app.repositories.dashboard import DashboardRepository
from app.schemas.dashboard import (
    AlertDistributionData,
    AlertDistributionResult,
    DashboardQueryParams,
    DashboardSummaryData,
    InventoryTrendData,
    InventoryUnitSummary,
    ProductRankingData,
    ProductRankingParams,
)
from app.services.dashboard_policy import (
    ensure_dashboard_warehouse_scope,
    require_dashboard_read,
    warehouse_ids_for_dashboard,
)


class DashboardService:
    """大屏只读业务门面，聚合结果不改变领域数据。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = DashboardRepository(session)

    async def summary(
        self, context: AuthContext, params: DashboardQueryParams
    ) -> DashboardSummaryData:
        require_dashboard_read(context)
        ensure_dashboard_warehouse_scope(context, params.warehouse_id)
        async with transaction_scope(self.session):
            raw = await self.repository.get_summary(
                context.cooperative_id,
                self._warehouse_scope(context, params.warehouse_id),
                today=datetime.now(UTC).date(),
            )
        return DashboardSummaryData(
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

    async def inventory_trends(
        self, context: AuthContext, params: DashboardQueryParams
    ) -> list[InventoryTrendData]:
        require_dashboard_read(context)
        ensure_dashboard_warehouse_scope(context, params.warehouse_id)
        start_date, end_date = resolve_dashboard_dates(params)
        async with transaction_scope(self.session):
            rows = await self.repository.inventory_trends(
                context.cooperative_id,
                self._warehouse_scope(context, params.warehouse_id),
                start_date=start_date,
                end_date=end_date,
            )
        return [
            InventoryTrendData(
                date=row[0],
                unit=row[1],
                inbound_quantity=float(row[2]),
                outbound_quantity=float(row[3]),
                ending_quantity=float(row[4]),
            )
            for row in rows
        ]

    async def alert_distribution(
        self, context: AuthContext, params: DashboardQueryParams
    ) -> AlertDistributionResult:
        require_dashboard_read(context)
        ensure_dashboard_warehouse_scope(context, params.warehouse_id)
        start_date, end_date = resolve_dashboard_dates(params)
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
        return AlertDistributionResult(
            total_count=sum(item.count for item in items), items=items
        )

    async def product_ranking(
        self, context: AuthContext, params: ProductRankingParams
    ) -> list[ProductRankingData]:
        require_dashboard_read(context)
        ensure_dashboard_warehouse_scope(context, params.warehouse_id)
        start_date, end_date = resolve_dashboard_dates(params)
        async with transaction_scope(self.session):
            rows = await self.repository.product_ranking(
                context.cooperative_id,
                self._warehouse_scope(context, params.warehouse_id),
                start_date=start_date,
                end_date=end_date,
                limit=params.limit,
            )
        return [
            ProductRankingData(
                product_id=row[0],
                product_name=row[1],
                unit=row[2],
                outbound_quantity=float(row[3]),
                outbound_count=row[4],
            )
            for row in rows
        ]

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
