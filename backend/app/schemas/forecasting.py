from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.models.enums import DataType, ModelType
from app.schemas.alerting import TaskData
from app.schemas.common import BaseSchema, PageParams


class ForecastHorizon(StrEnum):
    SEVEN_DAYS = "SEVEN_DAYS"
    THIRTY_DAYS = "THIRTY_DAYS"


class ForecastScope(BaseSchema):
    warehouse_id: UUID
    product_id: UUID


class TrainingRange(BaseSchema):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_order(self) -> TrainingRange:
        if self.end_date < self.start_date:
            raise ValueError("训练结束日期不能早于开始日期")
        return self


class ModelTrainingTaskCreate(BaseSchema):
    model_type: ModelType = ModelType.XGBOOST
    scope: ForecastScope
    training_range: TrainingRange
    test_ratio: float = Field(default=0.2, gt=0, lt=1)
    random_seed: int = Field(default=42, ge=0)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("model_type")
    @classmethod
    def only_xgboost_v1(cls, value: ModelType) -> ModelType:
        if value is not ModelType.XGBOOST:
            raise ValueError("V1 训练模型只支持 XGBOOST")
        return value


class ModelActivationCreate(BaseSchema):
    model_version_id: UUID


class ForecastTaskCreate(BaseSchema):
    warehouse_id: UUID
    product_id: UUID
    horizon: ForecastHorizon
    model_version_id: UUID | None = None

    @field_validator("horizon")
    @classmethod
    def validate_horizon(cls, value: ForecastHorizon) -> ForecastHorizon:
        if value not in {ForecastHorizon.SEVEN_DAYS, ForecastHorizon.THIRTY_DAYS}:
            raise ValueError("预测周期只支持 SEVEN_DAYS 或 THIRTY_DAYS")
        return value


class ModelVersionData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    warehouse_id: UUID
    product_id: UUID
    task_id: UUID | None
    model_type: ModelType
    version: str
    artifact_path: str | None
    data_type: DataType
    training_start_date: date
    training_end_date: date
    random_seed: int
    parameters: dict[str, Any]
    metrics: dict[str, Any]
    is_active: bool
    created_by: UUID
    created_at: Any


class ForecastPointData(BaseSchema):
    id: UUID
    forecast_result_id: UUID
    forecast_date: date
    predicted_quantity: float
    lower_bound: float
    upper_bound: float


class ForecastResultData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    warehouse_id: UUID
    product_id: UUID
    model_version_id: UUID
    task_id: UUID | None
    horizon_days: int
    forecast_start_date: date
    forecast_end_date: date
    predicted_demand: float
    current_stock: float
    recommended_replenishment: float
    data_type: DataType
    metrics: dict[str, Any]
    important_factors: list[str]
    limitation_notice: str
    generated_at: Any
    points: list[ForecastPointData] = Field(default_factory=list)


class ModelVersionListParams(PageParams):
    warehouse_id: UUID | None = None
    product_id: UUID | None = None
    is_active: bool | None = None


class ForecastResultListParams(PageParams):
    warehouse_id: UUID | None = None
    product_id: UUID | None = None


__all__ = [
    "ForecastHorizon",
    "ForecastPointData",
    "ForecastResultData",
    "ForecastResultListParams",
    "ForecastScope",
    "ForecastTaskCreate",
    "ModelActivationCreate",
    "ModelTrainingTaskCreate",
    "ModelVersionData",
    "ModelVersionListParams",
    "TaskData",
    "TrainingRange",
]
