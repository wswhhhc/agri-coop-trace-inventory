from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import permission_denied, resource_not_found
from app.core.auth.context import AuthContext
from app.infrastructure.transaction import transaction_scope
from app.models import (
    SYSTEM_ADMIN_ROLE_CODE,
    Batch,
    TraceEvent,
    TraceEventType,
)
from app.repositories.batch import BatchRepository
from app.repositories.traceability import TraceEventRepository
from app.schemas.traceability import TraceEventCreate, TraceEventListParams

TRACE_READ_PERMISSION = "trace:read"
WAREHOUSE_STAFF_ROLE_CODE = "WAREHOUSE_STAFF"


class TraceEventWriter:
    """在调用方业务事务内追加追溯事件，不自行提交事务。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = TraceEventRepository(session)

    async def record(
        self,
        *,
        batch: Batch,
        event_type: TraceEventType,
        title: str,
        event_time: datetime,
        description: str | None = None,
        source_type: str | None = None,
        source_id: UUID | None = None,
        public_data: Mapping[str, Any] | None = None,
        created_by: UUID | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            cooperative_id=batch.cooperative_id,
            batch_id=batch.id,
            event_type=event_type,
            title=title,
            description=description,
            event_time=event_time,
            source_type=source_type,
            source_id=source_id,
            public_data=dict(public_data or {}),
            created_by=created_by,
        )
        return await self.repository.add(event)

    async def record_from_payload(
        self,
        *,
        batch: Batch,
        payload: TraceEventCreate,
        created_by: UUID | None = None,
    ) -> TraceEvent:
        return await self.record(
            batch=batch,
            event_type=payload.event_type,
            title=payload.title,
            description=payload.description,
            event_time=payload.event_time,
            source_type=payload.source_type,
            source_id=payload.source_id,
            public_data=payload.public_data,
            created_by=created_by,
        )


class TraceabilityService:
    """内部追溯查询用例；公开投影在后续阶段实现。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TraceEventRepository(session)
        self.batch_repository = BatchRepository(session)

    async def list_internal(
        self,
        context: AuthContext,
        batch_id: UUID,
        params: TraceEventListParams | None = None,
    ) -> tuple[list[TraceEvent], int]:
        self._require_read(context)
        params = params or TraceEventListParams()
        async with transaction_scope(self.session):
            batch = await self.batch_repository.get_scoped(
                context.cooperative_id,
                self._warehouse_ids_for_query(context),
                batch_id,
            )
            if batch is None:
                raise resource_not_found()
            return await self.repository.list_scoped(
                context.cooperative_id,
                batch.id,
                event_type=params.event_type,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )

    @staticmethod
    def _require_read(context: AuthContext) -> None:
        if not context.has_permission(TRACE_READ_PERMISSION):
            raise permission_denied()

    @staticmethod
    def _warehouse_ids_for_query(context: AuthContext):
        if context.role_code == SYSTEM_ADMIN_ROLE_CODE:
            return None
        if context.role_code == WAREHOUSE_STAFF_ROLE_CODE:
            return context.warehouse_ids
        return None


__all__ = ["TRACE_READ_PERMISSION", "TraceEventWriter", "TraceabilityService"]
