from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.models import ForecastResult, ModelVersion, TaskRecord
from app.schemas.alerting import TaskData
from app.schemas.common import ApiResponse, ListResponse
from app.schemas.forecasting import (
    ForecastResultData,
    ForecastResultListParams,
    ForecastTaskCreate,
    ModelActivationCreate,
    ModelTrainingTaskCreate,
    ModelVersionData,
    ModelVersionListParams,
)
from app.services.forecasting import ForecastingService
from app.tasks.forecasting_tasks import forecast_demand_task, train_model_task

router = APIRouter(tags=["forecasting"])


def get_forecasting_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ForecastingService:
    return ForecastingService(session)


def _task_data(record: TaskRecord) -> TaskData:
    return TaskData.model_validate(record)


def _model_data(model: ModelVersion) -> ModelVersionData:
    return ModelVersionData.model_validate(model)


def _result_data(result: ForecastResult) -> ForecastResultData:
    return ForecastResultData.model_validate(result)


@router.post(
    "/model-training-tasks", response_model=ApiResponse[TaskData], status_code=202
)
async def submit_model_training_task(
    payload: ModelTrainingTaskCreate,
    context: CurrentAuthContext,
    service: Annotated[ForecastingService, Depends(get_forecasting_service)],
) -> ApiResponse[TaskData]:
    return ApiResponse(
        data=_task_data(
            await service.submit_model_training(
                context, payload, train_model_task.apply_async
            )
        )
    )


@router.get("/model-versions", response_model=ListResponse[ModelVersionData])
async def list_model_versions(
    params: Annotated[ModelVersionListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[ForecastingService, Depends(get_forecasting_service)],
) -> ListResponse[ModelVersionData]:
    items, total = await service.list_model_versions(context, params)
    return ListResponse(
        data=[_model_data(item) for item in items],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@router.get(
    "/model-versions/{modelVersionId}", response_model=ApiResponse[ModelVersionData]
)
async def get_model_version(
    model_version_id: Annotated[UUID, Path(alias="modelVersionId")],
    context: CurrentAuthContext,
    service: Annotated[ForecastingService, Depends(get_forecasting_service)],
) -> ApiResponse[ModelVersionData]:
    return ApiResponse(
        data=_model_data(await service.get_model_version(context, model_version_id))
    )


@router.post(
    "/model-activations", response_model=ApiResponse[ModelVersionData], status_code=201
)
async def activate_model(
    payload: ModelActivationCreate,
    context: CurrentAuthContext,
    service: Annotated[ForecastingService, Depends(get_forecasting_service)],
) -> ApiResponse[ModelVersionData]:
    return ApiResponse(data=_model_data(await service.activate_model(context, payload)))


@router.post("/forecast-tasks", response_model=ApiResponse[TaskData], status_code=202)
async def submit_forecast_task(
    payload: ForecastTaskCreate,
    context: CurrentAuthContext,
    service: Annotated[ForecastingService, Depends(get_forecasting_service)],
) -> ApiResponse[TaskData]:
    return ApiResponse(
        data=_task_data(
            await service.submit_forecast(
                context, payload, forecast_demand_task.apply_async
            )
        )
    )


@router.get("/forecast-results", response_model=ListResponse[ForecastResultData])
async def list_forecast_results(
    params: Annotated[ForecastResultListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[ForecastingService, Depends(get_forecasting_service)],
) -> ListResponse[ForecastResultData]:
    items, total = await service.list_forecast_results(context, params)
    return ListResponse(
        data=[_result_data(item) for item in items],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@router.get(
    "/forecast-results/{forecastResultId}",
    response_model=ApiResponse[ForecastResultData],
)
async def get_forecast_result(
    forecast_result_id: Annotated[UUID, Path(alias="forecastResultId")],
    context: CurrentAuthContext,
    service: Annotated[ForecastingService, Depends(get_forecasting_service)],
) -> ApiResponse[ForecastResultData]:
    return ApiResponse(
        data=_result_data(
            await service.get_forecast_result(context, forecast_result_id)
        )
    )


@router.get("/tasks/{taskId}", response_model=ApiResponse[TaskData])
async def get_forecasting_task(
    task_id: Annotated[UUID, Path(alias="taskId")],
    context: CurrentAuthContext,
    service: Annotated[ForecastingService, Depends(get_forecasting_service)],
) -> ApiResponse[TaskData]:
    return ApiResponse(data=_task_data(await service.get_task(context, task_id)))


__all__ = ["get_forecasting_service", "router"]
