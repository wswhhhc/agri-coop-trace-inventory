from datetime import UTC, date, datetime

import pytest
from app.ml.forecasting import (
    build_daily_demand_features,
    evaluate_forecast,
    moving_average_forecast,
    predict_xgboost,
    train_xgboost,
    validate_horizon,
)


def test_validate_horizon_only_accepts_supported_periods() -> None:
    assert validate_horizon("SEVEN_DAYS") == 7
    assert validate_horizon("THIRTY_DAYS") == 30
    assert validate_horizon(7) == 7
    with pytest.raises(ValueError, match="7 或 30"):
        validate_horizon(14)


def test_daily_features_aggregate_only_outbound_records_and_fill_missing_dates() -> (
    None
):
    records = [
        {
            "occurred_at": datetime(2026, 1, 1, 10, tzinfo=UTC),
            "quantity": 3,
            "transaction_type": "OUTBOUND",
        },
        {
            "occurred_at": datetime(2026, 1, 1, 15, tzinfo=UTC),
            "quantity": 2,
            "transaction_type": "OUTBOUND",
        },
        {
            "occurred_at": datetime(2026, 1, 2, 9, tzinfo=UTC),
            "quantity": 100,
            "transaction_type": "INBOUND",
        },
    ]
    frame = build_daily_demand_features(records, date(2026, 1, 1), date(2026, 1, 3))
    assert list(frame["date"]) == [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]
    assert list(frame["demand"]) == [5.0, 0.0, 0.0]
    assert {"day_of_week", "day_of_month", "month", "lag_1", "rolling_7"}.issubset(
        frame.columns
    )


def test_moving_average_forecast_is_nonnegative_and_repeats_latest_average() -> None:
    prediction = moving_average_forecast([1, 2, 3, -4], horizon_days=3, window=3)
    assert prediction == [pytest.approx(5 / 3)] * 3
    assert moving_average_forecast([], horizon_days=2) == [0.0, 0.0]


def test_evaluate_forecast_returns_mae_and_rmse() -> None:
    metrics = evaluate_forecast([1, 3], [2, 1])
    assert metrics == {"mae": pytest.approx(1.5), "rmse": pytest.approx(1.58113883)}


def test_train_xgboost_uses_fixed_features_and_nonnegative_predictions() -> None:
    frame = build_daily_demand_features([], date(2026, 1, 1), date(2026, 1, 4))
    model = train_xgboost(
        frame, [1, 2, 3, 4], parameters={"n_estimators": 2, "max_depth": 2}
    )
    predictions = predict_xgboost(model, frame)
    assert len(predictions) == 4
    assert all(float(value) >= 0 for value in predictions)
