from datetime import date
from decimal import Decimal
from inspect import isclass
from uuid import uuid4

from app.models import (
    Base,
    DataType,
    ForecastPoint,
    ForecastResult,
    ModelType,
    ModelVersion,
)
from sqlalchemy import inspect


def test_forecasting_models_are_registered_with_database_shape() -> None:
    assert all(
        isclass(model) for model in (ModelVersion, ForecastResult, ForecastPoint)
    )
    assert {"model_versions", "forecast_results", "forecast_points"}.issubset(
        Base.metadata.tables
    )
    assert {
        "id",
        "cooperative_id",
        "warehouse_id",
        "product_id",
        "task_id",
        "model_type",
        "version",
        "artifact_path",
        "data_type",
        "training_start_date",
        "training_end_date",
        "random_seed",
        "parameters",
        "metrics",
        "is_active",
        "created_by",
        "created_at",
    } == {column.name for column in inspect(ModelVersion).columns}
    assert {
        "id",
        "cooperative_id",
        "warehouse_id",
        "product_id",
        "model_version_id",
        "task_id",
        "horizon_days",
        "forecast_start_date",
        "forecast_end_date",
        "predicted_demand",
        "current_stock",
        "recommended_replenishment",
        "data_type",
        "metrics",
        "important_factors",
        "limitation_notice",
        "generated_at",
    } == {column.name for column in inspect(ForecastResult).columns}
    assert {
        "id",
        "forecast_result_id",
        "forecast_date",
        "predicted_quantity",
        "lower_bound",
        "upper_bound",
    } == {column.name for column in inspect(ForecastPoint).columns}


def test_forecasting_models_have_expected_enums_and_defaults() -> None:
    assert {item.value for item in ModelType} == {
        "MOVING_AVERAGE",
        "RANDOM_FOREST",
        "XGBOOST",
    }
    assert {item.value for item in DataType} == {"SYNTHETIC", "REAL"}
    assert inspect(ModelVersion).columns.model_type.type.enum_class is ModelType  # type: ignore[attr-defined]
    assert inspect(ModelVersion).columns.data_type.type.enum_class is DataType  # type: ignore[attr-defined]
    assert inspect(ForecastResult).columns.data_type.type.enum_class is DataType  # type: ignore[attr-defined]

    model = ModelVersion(
        cooperative_id=uuid4(),
        warehouse_id=uuid4(),
        product_id=uuid4(),
        model_type=ModelType.XGBOOST,
        version="xgb-1",
        data_type=DataType.SYNTHETIC,
        training_start_date=date(2026, 1, 1),
        training_end_date=date(2026, 1, 31),
        random_seed=42,
        created_by=uuid4(),
    )
    result = ForecastResult(
        cooperative_id=uuid4(),
        warehouse_id=uuid4(),
        product_id=uuid4(),
        model_version_id=model.id,
        horizon_days=7,
        forecast_start_date=date(2026, 2, 1),
        forecast_end_date=date(2026, 2, 7),
        predicted_demand=Decimal(10),
        current_stock=Decimal(3),
        recommended_replenishment=Decimal(7),
        data_type=DataType.SYNTHETIC,
        limitation_notice="synthetic",
    )
    point = ForecastPoint(
        forecast_result_id=result.id,
        forecast_date=date(2026, 2, 1),
        predicted_quantity=Decimal(1),
        lower_bound=Decimal(0),
        upper_bound=Decimal(2),
    )
    assert ModelVersion.__table__.c.is_active.default.arg is False
    assert callable(ForecastResult.__table__.c.important_factors.default.arg)
    assert point.upper_bound == 2
