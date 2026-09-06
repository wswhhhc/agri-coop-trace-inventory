from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta
from math import sqrt
from typing import Any

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

SUPPORTED_HORIZONS = {7, 30}
FEATURE_COLUMNS = (
    "day_of_week",
    "day_of_month",
    "month",
    "day_of_year",
    "lag_1",
    "lag_7",
    "rolling_7",
)


def validate_horizon(horizon: int | str) -> int:
    """将 API 的周期枚举转换为数据库使用的天数。"""
    values = {"SEVEN_DAYS": 7, "THIRTY_DAYS": 30}
    days = values.get(horizon, horizon) if isinstance(horizon, str) else horizon
    if days not in SUPPORTED_HORIZONS:
        raise ValueError("预测周期只支持 7 或 30 天")
    return int(days)


def _record_value(record: Any, key: str) -> Any:
    if isinstance(record, Mapping):
        return record.get(key)
    return getattr(record, key, None)


def build_daily_demand_features(
    records: Iterable[Any], start_date: date, end_date: date
) -> pd.DataFrame:
    """按日期聚合出库量并生成训练/预测共用的日历和滞后特征。"""
    if end_date < start_date:
        raise ValueError("结束日期不能早于开始日期")
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    demand_by_date: dict[date, float] = {}
    for record in records:
        transaction_type = _record_value(record, "transaction_type")
        if getattr(transaction_type, "value", transaction_type) != "OUTBOUND":
            continue
        occurred_at = _record_value(record, "occurred_at") or _record_value(
            record, "date"
        )
        quantity = _record_value(record, "quantity")
        if occurred_at is None or quantity is None:
            continue
        occurred_date = (
            occurred_at.date() if isinstance(occurred_at, datetime) else occurred_at
        )
        if (
            not isinstance(occurred_date, date)
            or not start_date <= occurred_date <= end_date
        ):
            continue
        demand_by_date[occurred_date] = demand_by_date.get(occurred_date, 0.0) + max(
            float(quantity), 0.0
        )
    frame = pd.DataFrame({"date": [item.date() for item in dates]})
    frame["demand"] = frame["date"].map(demand_by_date).fillna(0.0).astype(float)
    frame["day_of_week"] = pd.to_datetime(frame["date"]).dt.dayofweek
    frame["day_of_month"] = pd.to_datetime(frame["date"]).dt.day
    frame["month"] = pd.to_datetime(frame["date"]).dt.month
    frame["day_of_year"] = pd.to_datetime(frame["date"]).dt.dayofyear
    frame["lag_1"] = frame["demand"].shift(1).fillna(0.0)
    frame["lag_7"] = frame["demand"].shift(7).fillna(0.0)
    frame["rolling_7"] = (
        frame["demand"].shift(1).rolling(7, min_periods=1).mean().fillna(0.0)
    )
    return frame


def moving_average_forecast(
    history: Sequence[float], horizon_days: int, window: int = 7
) -> list[float]:
    """使用最近窗口的非负日需求均值生成基线预测。"""
    if horizon_days < 1:
        raise ValueError("预测天数必须大于 0")
    horizon = int(horizon_days)
    if window < 1:
        raise ValueError("移动平均窗口必须大于 0")
    values = [max(float(value), 0.0) for value in history[-window:]]
    average = sum(values) / len(values) if values else 0.0
    return [average] * horizon


def evaluate_forecast(
    actual: Sequence[float], predicted: Sequence[float]
) -> dict[str, float]:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("实际值与预测值必须非空且长度一致")
    errors = np.asarray(predicted, dtype=float) - np.asarray(actual, dtype=float)
    return {
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(sqrt(np.mean(errors**2))),
    }


def train_xgboost(
    features: pd.DataFrame,
    target: Sequence[float],
    *,
    parameters: Mapping[str, Any] | None = None,
    random_seed: int = 42,
) -> XGBRegressor:
    """训练可序列化的 XGBoost 回归器；训练特征列固定以避免推理漂移。"""
    missing = [column for column in FEATURE_COLUMNS if column not in features.columns]
    if missing:
        raise ValueError(f"缺少预测特征: {', '.join(missing)}")
    if len(features) != len(target) or len(features) < 2:
        raise ValueError("训练样本至少需要两条且特征与目标长度一致")
    params = dict(parameters or {})
    allowed = {
        "max_depth",
        "n_estimators",
        "learning_rate",
        "subsample",
        "colsample_bytree",
        "min_child_weight",
    }
    model_params = {key: value for key, value in params.items() if key in allowed}
    model = XGBRegressor(
        objective="reg:squarederror",
        random_state=random_seed,
        n_jobs=1,
        **model_params,
    )
    model.fit(
        features.loc[:, FEATURE_COLUMNS],
        np.maximum(np.asarray(target, dtype=float), 0.0),
    )
    return model


def predict_xgboost(model: XGBRegressor, features: pd.DataFrame) -> list[float]:
    """按训练时固定特征顺序预测，并将需求量截断为非负值。"""
    missing = [column for column in FEATURE_COLUMNS if column not in features.columns]
    if missing:
        raise ValueError(f"缺少预测特征: {', '.join(missing)}")
    values = model.predict(features.loc[:, FEATURE_COLUMNS])
    return [max(float(value), 0.0) for value in values]


def future_features(
    history: pd.DataFrame, start_date: date, horizon_days: int
) -> pd.DataFrame:
    """基于历史日特征构造未来日期特征，滞后值不足时使用最近滚动均值。"""
    horizon = validate_horizon(horizon_days)
    if history.empty or "date" not in history or "demand" not in history:
        raise ValueError("历史特征不能为空")
    values = list(history["demand"].astype(float))
    rows = []
    for offset in range(horizon):
        current = start_date + timedelta(days=offset)
        recent = values[-7:] or [0.0]
        rows.append(
            {
                "date": current,
                "day_of_week": current.weekday(),
                "day_of_month": current.day,
                "month": current.month,
                "day_of_year": current.timetuple().tm_yday,
                "lag_1": values[-1] if values else 0.0,
                "lag_7": values[-7] if len(values) >= 7 else 0.0,
                "rolling_7": sum(recent) / len(recent),
            }
        )
        values.append(rows[-1]["rolling_7"])
    return pd.DataFrame(rows)


__all__ = [
    "FEATURE_COLUMNS",
    "build_daily_demand_features",
    "evaluate_forecast",
    "future_features",
    "moving_average_forecast",
    "predict_xgboost",
    "train_xgboost",
    "validate_horizon",
]
