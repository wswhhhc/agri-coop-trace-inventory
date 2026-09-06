from datetime import date
from uuid import uuid4

import pytest
from app.schemas.forecasting import (
    ForecastHorizon,
    ForecastTaskCreate,
    ModelActivationCreate,
    ModelTrainingTaskCreate,
    TrainingRange,
)
from pydantic import ValidationError


def test_forecasting_requests_validate_scope_horizon_and_dates() -> None:
    warehouse_id, product_id = uuid4(), uuid4()
    payload = ModelTrainingTaskCreate(
        model_type="XGBOOST",
        scope={"warehouseId": warehouse_id, "productId": product_id},
        training_range={"startDate": date(2026, 1, 1), "endDate": date(2026, 3, 1)},
    )
    assert payload.scope.warehouse_id == warehouse_id
    assert payload.model_type.value == "XGBOOST"
    assert (
        ForecastTaskCreate(
            warehouse_id=warehouse_id, product_id=product_id, horizon="SEVEN_DAYS"
        ).horizon
        is ForecastHorizon.SEVEN_DAYS
    )
    assert ModelActivationCreate(model_version_id=uuid4())
    with pytest.raises(ValidationError):
        TrainingRange(start_date=date(2026, 3, 1), end_date=date(2026, 1, 1))
    with pytest.raises(ValidationError):
        ForecastTaskCreate(
            warehouse_id=warehouse_id, product_id=product_id, horizon="14_DAYS"
        )


def test_model_training_rejects_non_xgboost_v1() -> None:
    with pytest.raises(ValidationError, match="XGBOOST"):
        ModelTrainingTaskCreate(
            model_type="RANDOM_FOREST",
            scope={"warehouseId": uuid4(), "productId": uuid4()},
            training_range={"startDate": date(2026, 1, 1), "endDate": date(2026, 2, 1)},
        )
