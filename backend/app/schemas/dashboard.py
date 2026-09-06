from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from app.schemas.common import BaseSchema


class DashboardQueryParams(BaseSchema):
    """大屏通用筛选；未提供日期时由服务层补齐最近 30 个自然日。"""

    warehouse_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> DashboardQueryParams:
        if self.start_date is None or self.end_date is None:
            return self
        if self.start_date > self.end_date:
            raise ValueError("开始日期不能晚于结束日期")
        if (self.end_date - self.start_date).days > 365:
            raise ValueError("查询时间范围不能超过 366 天")
        return self


class ProductRankingParams(DashboardQueryParams):
    limit: int = Field(default=10, ge=1, le=100)


class InventoryUnitSummary(BaseSchema):
    unit: str
    quantity: float


class DashboardSummaryData(BaseSchema):
    product_count: int
    batch_count: int
    inventory_by_unit: list[InventoryUnitSummary]
    pending_alert_count: int
    expiring_batch_count: int
    low_stock_product_count: int
    updated_at: AwareDatetime


class InventoryTrendData(BaseSchema):
    date: date
    unit: str
    inbound_quantity: float
    outbound_quantity: float
    ending_quantity: float


class AlertDistributionData(BaseSchema):
    alert_type: str
    severity: str
    count: int


class AlertDistributionResult(BaseSchema):
    total_count: int
    items: list[AlertDistributionData]


class ProductRankingData(BaseSchema):
    product_id: UUID
    product_name: str
    unit: str
    outbound_quantity: float
    outbound_count: int


class ForecastComparisonData(BaseSchema):
    forecast_result_id: UUID
    warehouse_id: UUID
    product_id: UUID
    model_version_id: UUID
    model_version: str
    forecast_start_date: date
    forecast_end_date: date
    predicted_demand: float
    actual_demand: float
    absolute_error: float
    metrics: dict[str, float]


__all__ = [
    "AlertDistributionData",
    "AlertDistributionResult",
    "DashboardQueryParams",
    "DashboardSummaryData",
    "ForecastComparisonData",
    "InventoryTrendData",
    "InventoryUnitSummary",
    "ProductRankingData",
    "ProductRankingParams",
]
