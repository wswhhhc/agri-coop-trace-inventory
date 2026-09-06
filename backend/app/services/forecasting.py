from __future__ import annotations

from collections.abc import Callable
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import resource_not_found
from app.core.auth.context import AuthContext
from app.infrastructure.transaction import transaction_scope
from app.models import ForecastResult, ModelVersion, TaskRecord, TaskStatus
from app.repositories.forecasting import ForecastingRepository
from app.schemas.forecasting import (
    ForecastResultListParams,
    ForecastTaskCreate,
    ModelActivationCreate,
    ModelTrainingTaskCreate,
    ModelVersionListParams,
)
from app.services.forecasting_policy import (
    require_model_manage,
    require_model_read,
    warehouse_ids_for_query,
)


class ForecastingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ForecastingRepository(session)

    async def submit_model_training(
        self,
        context: AuthContext,
        payload: ModelTrainingTaskCreate,
        enqueue: Callable[..., object],
    ) -> TaskRecord:
        require_model_manage(context)
        if context.cooperative_id is None or not context.has_warehouse_access(
            payload.scope.warehouse_id
        ):
            raise resource_not_found()
        celery_task_id = str(uuid4())
        async with transaction_scope(self.session):
            warehouse = await self.repository.get_warehouse(
                context.cooperative_id, payload.scope.warehouse_id
            )
            product = await self.repository.get_product(
                context.cooperative_id, payload.scope.product_id
            )
            if warehouse is None or product is None:
                raise resource_not_found()
            record = await self.repository.add_task(
                TaskRecord(
                    cooperative_id=context.cooperative_id,
                    task_type="MODEL_TRAINING",
                    celery_task_id=celery_task_id,
                    status=TaskStatus.PENDING,
                    requested_by=context.user_id,
                    request_payload=payload.model_dump(mode="json", by_alias=True),
                )
            )
        try:
            enqueue(args=[str(record.id)], kwargs={}, task_id=celery_task_id)
        except Exception as error:
            async with transaction_scope(self.session):
                failed = await self.session.get(
                    TaskRecord, record.id, with_for_update=True
                )
                if failed is not None:
                    failed.status = TaskStatus.FAILURE
                    failed.error_code = "TASK_SUBMIT_FAILED"
                    failed.error_message = str(error)[:500]
            raise
        return record

    async def list_model_versions(
        self, context: AuthContext, params: ModelVersionListParams
    ) -> tuple[list[ModelVersion], int]:
        require_model_read(context)
        if params.warehouse_id is not None and not context.has_warehouse_access(
            params.warehouse_id
        ):
            raise resource_not_found()
        async with transaction_scope(self.session):
            return await self.repository.list_model_versions(
                context.cooperative_id,
                warehouse_ids_for_query(context),
                warehouse_id=params.warehouse_id,
                product_id=params.product_id,
                is_active=params.is_active,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order.value,
            )

    async def get_model_version(
        self, context: AuthContext, model_version_id: UUID
    ) -> ModelVersion:
        require_model_read(context)
        async with transaction_scope(self.session):
            version = await self.repository.get_model_version(
                context.cooperative_id,
                warehouse_ids_for_query(context),
                model_version_id,
            )
            if version is None:
                raise resource_not_found()
            return version

    async def activate_model(
        self, context: AuthContext, payload: ModelActivationCreate
    ) -> ModelVersion:
        require_model_manage(context)
        async with transaction_scope(self.session):
            version = await self.repository.get_model_version(
                context.cooperative_id, None, payload.model_version_id, lock=True
            )
            if version is None:
                raise resource_not_found()
            await self.repository.deactivate_scope(
                version.cooperative_id, version.warehouse_id, version.product_id
            )
            version.is_active = True
            await self.session.flush()
            return version

    async def submit_forecast(
        self,
        context: AuthContext,
        payload: ForecastTaskCreate,
        enqueue: Callable[..., object],
    ) -> TaskRecord:
        require_model_manage(context)
        if context.cooperative_id is None or not context.has_warehouse_access(
            payload.warehouse_id
        ):
            raise resource_not_found()
        celery_task_id = str(uuid4())
        async with transaction_scope(self.session):
            if (
                await self.repository.get_warehouse(
                    context.cooperative_id, payload.warehouse_id
                )
                is None
                or await self.repository.get_product(
                    context.cooperative_id, payload.product_id
                )
                is None
            ):
                raise resource_not_found()
            model = (
                await self.repository.get_model_version(
                    context.cooperative_id, None, payload.model_version_id
                )
                if payload.model_version_id
                else await self.repository.get_active_model(
                    context.cooperative_id, payload.warehouse_id, payload.product_id
                )
            )
            if (
                model is None
                or model.warehouse_id != payload.warehouse_id
                or model.product_id != payload.product_id
            ):
                raise resource_not_found()
            record = await self.repository.add_task(
                TaskRecord(
                    cooperative_id=context.cooperative_id,
                    task_type="DEMAND_FORECAST",
                    celery_task_id=celery_task_id,
                    status=TaskStatus.PENDING,
                    requested_by=context.user_id,
                    request_payload=payload.model_dump(mode="json", by_alias=True),
                )
            )
        try:
            enqueue(args=[str(record.id)], kwargs={}, task_id=celery_task_id)
        except Exception as error:
            async with transaction_scope(self.session):
                failed = await self.session.get(
                    TaskRecord, record.id, with_for_update=True
                )
                if failed is not None:
                    failed.status = TaskStatus.FAILURE
                    failed.error_code = "TASK_SUBMIT_FAILED"
                    failed.error_message = str(error)[:500]
            raise
        return record

    async def list_forecast_results(
        self, context: AuthContext, params: ForecastResultListParams
    ) -> tuple[list[ForecastResult], int]:
        require_model_read(context)
        if params.warehouse_id is not None and not context.has_warehouse_access(
            params.warehouse_id
        ):
            raise resource_not_found()
        async with transaction_scope(self.session):
            return await self.repository.list_forecast_results(
                context.cooperative_id,
                warehouse_ids_for_query(context),
                warehouse_id=params.warehouse_id,
                product_id=params.product_id,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order.value,
            )

    async def get_forecast_result(
        self, context: AuthContext, result_id: UUID
    ) -> ForecastResult:
        require_model_read(context)
        async with transaction_scope(self.session):
            result = await self.repository.get_forecast_result(
                context.cooperative_id, warehouse_ids_for_query(context), result_id
            )
            if result is None:
                raise resource_not_found()
            return result

    async def get_task(self, context: AuthContext, task_id: UUID) -> TaskRecord:
        require_model_read(context)
        can_manage = context.role_code in {"SYSTEM_ADMIN", "COOPERATIVE_ADMIN"}
        async with transaction_scope(self.session):
            task = await self.repository.get_task(
                task_id, context.cooperative_id, context.user_id, can_manage
            )
            if task is None:
                raise resource_not_found()
            return task


__all__ = ["ForecastingService"]
