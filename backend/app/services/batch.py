from __future__ import annotations

import secrets
from datetime import UTC, date, datetime, time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import (
    ensure_warehouse_scope,
    permission_denied,
    resource_not_found,
)
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException, StatusNotAllowedError
from app.core.validation import require_non_empty_update
from app.infrastructure.transaction import transaction_scope
from app.models import (
    Batch,
    BatchStatus,
    TraceEventType,
)
from app.repositories.batch import BatchRepository
from app.repositories.product import ProductRepository
from app.schemas.batch import BatchCreate, BatchListParams, BatchUpdate
from app.services.batch_policy import (
    WAREHOUSE_STAFF_ROLE_CODE,
    require_manage,
    require_read_role,
    warehouse_ids_for_query,
)
from app.services.traceability import TraceabilityCache, TraceEventWriter

_ALLOWED_STATUS_TRANSITIONS: dict[BatchStatus, frozenset[BatchStatus]] = {
    BatchStatus.CREATED: frozenset(
        {BatchStatus.IN_STOCK, BatchStatus.BLOCKED, BatchStatus.EXPIRED}
    ),
    BatchStatus.IN_STOCK: frozenset(
        {BatchStatus.DEPLETED, BatchStatus.BLOCKED, BatchStatus.EXPIRED}
    ),
    BatchStatus.BLOCKED: frozenset({BatchStatus.CREATED, BatchStatus.EXPIRED}),
    BatchStatus.DEPLETED: frozenset(),
    BatchStatus.EXPIRED: frozenset(),
}


class BatchService:
    """批次业务用例，负责产品启用状态和批次状态流转。"""

    def __init__(
        self, session: AsyncSession, cache: TraceabilityCache | None = None
    ) -> None:
        self.session = session
        self.repository = BatchRepository(session)
        self.product_repository = ProductRepository(session)
        self.trace_writer = TraceEventWriter(session)
        self.trace_cache = cache

    @staticmethod
    def ensure_read_access(context: AuthContext) -> None:
        require_read_role(context)

    async def list(
        self,
        context: AuthContext,
        params: BatchListParams,
    ) -> tuple[list[Batch], int]:
        require_read_role(context)
        if params.warehouse_id is not None:
            ensure_warehouse_scope(context, params.warehouse_id)
        async with transaction_scope(self.session):
            return await self.repository.list_scoped(
                context.cooperative_id,
                warehouse_ids_for_query(context),
                keyword=params.keyword,
                product_id=params.product_id,
                warehouse_id=params.warehouse_id,
                status=params.status,
                production_date_from=params.production_date_from,
                production_date_to=params.production_date_to,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )

    async def get(self, context: AuthContext, batch_id: UUID) -> Batch:
        require_read_role(context)
        async with transaction_scope(self.session):
            batch = await self.repository.get_scoped(
                context.cooperative_id,
                warehouse_ids_for_query(context),
                batch_id,
            )
            if batch is None:
                raise resource_not_found()
            return batch

    async def create(self, context: AuthContext, payload: BatchCreate) -> Batch:
        require_manage(context)
        cooperative_id = self._require_cooperative(context)
        self._require_warehouse_access(context)
        async with transaction_scope(self.session):
            product = await self.product_repository.get_scoped(
                cooperative_id,
                warehouse_ids_for_query(context),
                payload.product_id,
            )
            if product is None:
                raise resource_not_found()
            if not product.is_active:
                raise AppException(
                    code="PRODUCT_DISABLED",
                    message="停用产品不能创建新批次",
                    status_code=409,
                )
            batch = Batch(
                cooperative_id=cooperative_id,
                product_id=product.id,
                batch_no=self._new_batch_no(product.code, payload.production_date),
                trace_code=self._new_trace_code(),
                origin=payload.origin,
                production_date=payload.production_date,
                expiry_date=payload.expiry_date,
                responsible_person=payload.responsible_person,
                status=BatchStatus.CREATED,
                created_by=context.user_id,
            )
            created = await self.repository.add(batch)
            await self.trace_writer.record(
                batch=created,
                event_type=TraceEventType.PRODUCTION,
                title="生产批次建立",
                description="批次信息已登记",
                event_time=datetime.combine(payload.production_date, time.min, tzinfo=UTC),
                source_type="BATCH",
                source_id=created.id,
                created_by=context.user_id,
            )
        await self._invalidate_trace_cache(created.trace_code)
        return created

    async def update(
        self,
        context: AuthContext,
        batch_id: UUID,
        payload: BatchUpdate,
    ) -> Batch:
        require_manage(context)
        async with transaction_scope(self.session):
            batch = await self.repository.get_scoped(
                context.cooperative_id,
                warehouse_ids_for_query(context),
                batch_id,
            )
            if batch is None:
                raise resource_not_found()
            if (
                context.role_code == WAREHOUSE_STAFF_ROLE_CODE
                and batch.created_by != context.user_id
            ):
                raise permission_denied()
            values = require_non_empty_update(payload.model_dump(exclude_unset=True))
            if "expiry_date" in values and values["expiry_date"] < batch.production_date:
                raise AppException(
                    code="BAD_REQUEST",
                    message="到期日期不能早于生产日期",
                    status_code=400,
                )
            requested_status = values.get("status")
            if requested_status is not None and requested_status != batch.status:
                allowed = _ALLOWED_STATUS_TRANSITIONS[batch.status]
                if requested_status not in allowed:
                    raise StatusNotAllowedError(
                        current_status=batch.status.value,
                        allowed_statuses=sorted(status.value for status in allowed),
                    )
            updated = await self.repository.update(batch, values)
        await self._invalidate_trace_cache(updated.trace_code)
        return updated

    async def _invalidate_trace_cache(self, trace_code: str) -> None:
        if self.trace_cache is not None:
            await self.trace_cache.invalidate(trace_code)

    @staticmethod
    def _new_batch_no(product_code: str, production_date: date) -> str:
        normalized_code = "".join(
            character if character.isalnum() else "-"
            for character in product_code.upper()
        ).strip("-") or "PRODUCT"
        return f"{normalized_code}-{production_date:%Y%m%d}-{secrets.token_hex(3).upper()}"

    @staticmethod
    def _new_trace_code() -> str:
        return f"tr_{secrets.token_urlsafe(9)}"

    @staticmethod
    def _require_cooperative(context: AuthContext) -> UUID:
        if context.cooperative_id is None:
            raise AppException(
                code="BAD_REQUEST",
                message="批次必须关联合作社",
                status_code=400,
            )
        return context.cooperative_id

    @staticmethod
    def _require_warehouse_access(context: AuthContext) -> None:
        if (
            context.role_code == WAREHOUSE_STAFF_ROLE_CODE
            and not context.warehouse_ids
        ):
            raise resource_not_found()

__all__ = ["BatchService"]
