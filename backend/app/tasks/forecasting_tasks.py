"""需求预测 Celery 入口和可复现的训练/预测流水线。"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID

import joblib  # type: ignore[import-untyped]
from celery import Task  # type: ignore[import-untyped]

from app.core.config import get_settings
from app.infrastructure.database import create_database_engine, create_session_factory
from app.infrastructure.redis import create_redis_client
from app.ml.forecasting import (
    build_daily_demand_features,
    evaluate_forecast,
    future_features,
    moving_average_forecast,
    predict_xgboost,
    train_xgboost,
    validate_horizon,
)
from app.models import (
    DataType,
    ForecastPoint,
    ForecastResult,
    ModelType,
    ModelVersion,
    TaskRecord,
    TaskStatus,
)
from app.repositories.forecasting import ForecastingRepository
from app.services.query_cache import QueryCache
from app.tasks.celery_app import celery_app

LIMITATION_NOTICE = "结果基于合成数据，仅用于验证算法流程，不代表真实经营效果。"


@celery_app.task(
    bind=True,
    name="app.tasks.forecasting_tasks.train_model_task",
    acks_late=True,
    track_started=True,
)
def train_model_task(self: Task, task_record_id: str) -> dict[str, str]:
    return asyncio.run(_run_training(UUID(task_record_id), self.request.id))


@celery_app.task(
    bind=True,
    name="app.tasks.forecasting_tasks.forecast_demand_task",
    acks_late=True,
    track_started=True,
)
def forecast_demand_task(self: Task, task_record_id: str) -> dict[str, str]:
    return asyncio.run(_run_forecast(UUID(task_record_id), self.request.id))


async def _set_task(session, task_id: UUID, **values) -> TaskRecord | None:
    record = await session.get(TaskRecord, task_id, with_for_update=True)
    if record is not None:
        for key, value in values.items():
            setattr(record, key, value)
        await session.flush()
    return record


async def _run_training(task_id: UUID, celery_task_id: str) -> dict[str, str]:
    settings = get_settings()
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    try:
        async with factory() as session, session.begin():
            record = await _set_task(
                session,
                task_id,
                status=TaskStatus.RUNNING,
                progress=10,
                started_at=datetime.now(UTC),
            )
            if record is None:
                raise ValueError("预测训练任务不存在")
            payload = record.request_payload
            scope = payload.get("scope", {})
            range_payload = (
                payload.get("trainingRange") or payload.get("training_range") or {}
            )
            start = date.fromisoformat(
                range_payload.get("startDate") or range_payload["start_date"]
            )
            end = date.fromisoformat(
                range_payload.get("endDate") or range_payload["end_date"]
            )
            cooperative_id = record.cooperative_id
            if cooperative_id is None:
                raise ValueError("训练任务缺少合作社范围")
            warehouse_id = UUID(scope.get("warehouseId") or scope["warehouse_id"])
            product_id = UUID(scope.get("productId") or scope["product_id"])
            repository = ForecastingRepository(session)
            history = await repository.list_outbound_transactions(
                cooperative_id,
                warehouse_id,
                product_id,
                start,
                end + timedelta(days=1),
            )
            frame = build_daily_demand_features(history, start, end)
            split = max(
                1,
                min(
                    len(frame) - 1,
                    int(
                        len(frame)
                        * (
                            1
                            - float(
                                payload.get("testRatio", payload.get("test_ratio", 0.2))
                            )
                        )
                    ),
                ),
            )
            model = train_xgboost(
                frame.iloc[:split],
                frame["demand"].iloc[:split].tolist(),
                parameters=payload.get("parameters", {}),
                random_seed=int(
                    payload.get(
                        "randomSeed",
                        payload.get("random_seed", settings.ml_random_seed),
                    )
                ),
            )
            predictions = predict_xgboost(model, frame.iloc[split:])
            actual = frame["demand"].iloc[split:].tolist()
            metrics = evaluate_forecast(actual, predictions)
            baseline = moving_average_forecast(
                frame["demand"].iloc[:split].tolist(), len(actual), window=7
            )
            metrics.update(
                {
                    f"baseline{key.title()}": value
                    for key, value in evaluate_forecast(actual, baseline).items()
                }
            )
            artifact_dir = Path(settings.model_artifact_dir)
            artifact_dir.mkdir(parents=True, exist_ok=True)
            version_name = f"xgb-{datetime.now(UTC):%Y%m%d%H%M%S}-{str(task_id)[:8]}"
            artifact_path = artifact_dir / f"{version_name}.joblib"
            joblib.dump(model, artifact_path)
            if record.requested_by is None:
                raise ValueError("训练任务缺少发起人")
            version = await repository.add_model_version(
                ModelVersion(
                    cooperative_id=cooperative_id,
                    warehouse_id=warehouse_id,
                    product_id=product_id,
                    task_id=task_id,
                    model_type=ModelType.XGBOOST,
                    version=version_name,
                    artifact_path=str(artifact_path),
                    data_type=DataType.SYNTHETIC,
                    training_start_date=start,
                    training_end_date=end,
                    random_seed=int(
                        payload.get(
                            "randomSeed",
                            payload.get("random_seed", settings.ml_random_seed),
                        )
                    ),
                    parameters=payload.get("parameters", {}),
                    metrics=metrics,
                    created_by=record.requested_by,
                )
            )
            await _set_task(
                session,
                task_id,
                status=TaskStatus.SUCCESS,
                progress=100,
                finished_at=datetime.now(UTC),
                result_payload={"modelVersionId": str(version.id)},
            )
            result = {"modelVersionId": str(version.id)}
        await _invalidate_forecasting_cache(settings, cooperative_id)
        return result
    except Exception as error:
        async with factory() as session, session.begin():
            await _set_task(
                session,
                task_id,
                status=TaskStatus.FAILURE,
                progress=100,
                finished_at=datetime.now(UTC),
                error_code="MODEL_TRAINING_FAILED",
                error_message=str(error)[:500],
            )
        raise
    finally:
        await engine.dispose()


async def _invalidate_forecasting_cache(settings, cooperative_id: UUID) -> None:
    """训练成功后清理模型版本查询缓存；缓存故障不影响任务结果。"""
    redis = create_redis_client(settings)
    try:
        cache = QueryCache(
            redis,
            key_prefix=settings.redis_key_prefix,
            ttl_seconds=settings.forecasting_cache_ttl_seconds,
            jitter_ratio=settings.cache_ttl_jitter_ratio,
            enabled=settings.query_cache_enabled,
            name="forecasting",
        )
        await cache.invalidate_resource("model-version-list", cooperative_id)
        await cache.invalidate_resource("model-version-detail", cooperative_id)
    finally:
        await redis.aclose()


async def _run_forecast(task_id: UUID, celery_task_id: str) -> dict[str, str]:
    settings = get_settings()
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    try:
        async with factory() as session, session.begin():
            record = await _set_task(
                session,
                task_id,
                status=TaskStatus.RUNNING,
                progress=10,
                started_at=datetime.now(UTC),
            )
            if record is None or record.cooperative_id is None:
                raise ValueError("需求预测任务不存在或缺少合作社范围")
            payload = record.request_payload
            warehouse_id, product_id = (
                UUID(payload.get("warehouseId") or payload["warehouse_id"]),
                UUID(payload.get("productId") or payload["product_id"]),
            )
            horizon = validate_horizon(payload.get("horizon", 7))
            repository = ForecastingRepository(session)
            model_id = payload.get("modelVersionId") or payload.get("model_version_id")
            model = (
                await repository.get_model_version(
                    record.cooperative_id, None, UUID(model_id)
                )
                if model_id
                else await repository.get_active_model(
                    record.cooperative_id, warehouse_id, product_id
                )
            )
            if (
                model is None
                or model.warehouse_id != warehouse_id
                or model.product_id != product_id
            ):
                raise ValueError("未找到可用的预测模型")
            end = datetime.now(UTC).date()
            start = end - timedelta(days=90)
            history = await repository.list_outbound_transactions(
                record.cooperative_id,
                warehouse_id,
                product_id,
                start,
                end + timedelta(days=1),
            )
            frame = build_daily_demand_features(history, start, end)
            if model.artifact_path and Path(model.artifact_path).exists():
                predictions = predict_xgboost(
                    joblib.load(model.artifact_path),
                    future_features(frame, end + timedelta(days=1), horizon),
                )
            else:
                predictions = moving_average_forecast(frame["demand"].tolist(), horizon)
            current_stock = await repository.current_stock(
                record.cooperative_id, warehouse_id, product_id
            )
            total = sum(predictions)
            product = await repository.get_product(record.cooperative_id, product_id)
            replenishment = max(
                total
                + float(getattr(product, "safety_stock", 0))
                - float(current_stock),
                0.0,
            )
            result = await repository.add_forecast_result(
                ForecastResult(
                    cooperative_id=record.cooperative_id,
                    warehouse_id=warehouse_id,
                    product_id=product_id,
                    model_version_id=model.id,
                    task_id=task_id,
                    horizon_days=horizon,
                    forecast_start_date=end + timedelta(days=1),
                    forecast_end_date=end + timedelta(days=horizon),
                    predicted_demand=total,
                    current_stock=current_stock,
                    recommended_replenishment=replenishment,
                    data_type=model.data_type,
                    metrics=model.metrics,
                    important_factors=["最近7日出库量", "月份", "星期"],
                    limitation_notice=LIMITATION_NOTICE,
                    points=[
                        ForecastPoint(
                            forecast_date=end + timedelta(days=index + 1),
                            predicted_quantity=value,
                            lower_bound=value * 0.8,
                            upper_bound=value * 1.2,
                        )
                        for index, value in enumerate(predictions)
                    ],
                )
            )
            await _set_task(
                session,
                task_id,
                status=TaskStatus.SUCCESS,
                progress=100,
                finished_at=datetime.now(UTC),
                result_payload={"forecastResultId": str(result.id)},
            )
            return {"forecastResultId": str(result.id)}
    except Exception as error:
        async with factory() as session, session.begin():
            await _set_task(
                session,
                task_id,
                status=TaskStatus.FAILURE,
                progress=100,
                finished_at=datetime.now(UTC),
                error_code="DEMAND_FORECAST_FAILED",
                error_message=str(error)[:500],
            )
        raise
    finally:
        await engine.dispose()


__all__ = ["forecast_demand_task", "train_model_task"]
