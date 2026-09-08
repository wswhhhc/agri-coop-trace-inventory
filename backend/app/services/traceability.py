from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import permission_denied, resource_not_found
from app.core.auth.context import AuthContext
from app.infrastructure.cache import JsonCache
from app.infrastructure.transaction import transaction_scope
from app.models import (
    SYSTEM_ADMIN_ROLE_CODE,
    Batch,
    TraceEvent,
    TraceEventType,
)
from app.repositories.batch import BatchRepository
from app.repositories.traceability import TraceEventRepository
from app.schemas.traceability import (
    PublicTraceBatchData,
    PublicTraceData,
    PublicTraceInspectionData,
    PublicTraceInspectionItemData,
    PublicTraceProductData,
    PublicTraceTimelineEventData,
    TraceEventCreate,
    TraceEventListParams,
)

TRACE_READ_PERMISSION = "trace:read"
WAREHOUSE_STAFF_ROLE_CODE = "WAREHOUSE_STAFF"
PUBLIC_TRACE_DATA_NOTICE = "本系统为毕业设计原型，当前演示数据为合成数据。"


class TraceabilityCache:
    """公开追溯缓存；Redis 故障时允许回源数据库。"""

    def __init__(self, redis: Any, *, key_prefix: str, ttl_seconds: int) -> None:
        self._cache = JsonCache(
            redis,
            key_prefix=key_prefix,
            ttl_seconds=ttl_seconds,
            name="traceability",
        )
        self.key_prefix = key_prefix

    def key(self, trace_code: str) -> str:
        return f"{self.key_prefix}trace:{trace_code}"

    async def get(self, trace_code: str) -> dict[str, Any] | None:
        payload = await self._cache.get(self.key(trace_code))
        return payload if isinstance(payload, dict) else None

    async def set(self, trace_code: str, payload: Mapping[str, Any]) -> None:
        await self._cache.set(self.key(trace_code), payload)

    async def invalidate(self, trace_code: str) -> None:
        await self._cache.delete(self.key(trace_code))


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


class PublicTraceabilityService:
    """通过追溯码查询公开脱敏投影，不直接序列化 ORM。"""

    def __init__(self, session: AsyncSession, cache: TraceabilityCache) -> None:
        self.session = session
        self.repository = TraceEventRepository(session)
        self.cache = cache

    async def get_public(self, trace_code: str) -> PublicTraceData:
        cached = await self.cache.get(trace_code)
        if cached is not None:
            try:
                return PublicTraceData.model_validate(cached)
            except ValidationError:
                await self.cache.invalidate(trace_code)

        async with transaction_scope(self.session):
            batch = await self.repository.get_public_batch(trace_code)
            if batch is None:
                raise resource_not_found()
            result = self._project(batch)

        await self.cache.set(
            trace_code, result.model_dump(mode="json", by_alias=True)
        )
        return result

    @staticmethod
    def _project(batch: Batch) -> PublicTraceData:
        inspections = sorted(
            batch.quality_inspections,
            # 同一天录入的质检时间均为 00:00，需用创建时间判断哪条是
            # 更正后的最新记录，UUID 仅作为完全相同时的稳定决胜字段。
            key=lambda inspection: (
                inspection.inspected_at,
                inspection.created_at,
                inspection.id,
            ),
            reverse=True,
        )
        latest_inspection = (
            PublicTraceInspectionData(
                inspection_date=inspection.inspected_at.date(),
                conclusion=inspection.conclusion,
                items=[
                    PublicTraceInspectionItemData(
                        name=item.item_name,
                        value=item.result_value,
                        unit=item.unit,
                        standard=item.standard_value,
                        is_qualified=item.is_qualified,
                    )
                    for item in inspection.items
                ],
            )
            if (inspection := (inspections[0] if inspections else None)) is not None
            else None
        )
        events = sorted(
            batch.trace_events,
            key=lambda event: (event.event_time, event.id),
        )
        timeline = [
            PublicTraceTimelineEventData(
                event_type=event.event_type,
                title=event.title,
                description=PublicTraceabilityService._public_event_description(event),
                occurred_at=event.event_time,
            )
            for event in events
        ]
        timestamps = [batch.created_at, *(event.created_at for event in events)]
        return PublicTraceData(
            trace_code=batch.trace_code,
            product=PublicTraceProductData(
                name=batch.product.name,
                category_name=batch.product.category.name,
                unit=batch.product.unit,
            ),
            batch=PublicTraceBatchData(
                batch_no=batch.batch_no,
                origin=batch.origin,
                production_date=batch.production_date,
                expiry_date=batch.expiry_date,
                status=batch.status,
            ),
            latest_inspection=latest_inspection,
            timeline=timeline,
            data_notice=PUBLIC_TRACE_DATA_NOTICE,
            updated_at=max(timestamps),
        )

    @staticmethod
    def _public_event_description(event: TraceEvent) -> str:
        if event.event_type is TraceEventType.PRODUCTION:
            return "批次信息已登记"
        if event.event_type is TraceEventType.INSPECTION:
            conclusion = event.public_data.get("conclusion")
            return (
                f"检验结论：{conclusion}"
                if isinstance(conclusion, str)
                else "已完成质量检验"
            )
        descriptions = {
            TraceEventType.INBOUND: "产品已完成入库",
            TraceEventType.OUTBOUND: "产品已完成出库",
            TraceEventType.TRANSFER: "产品已完成调拨",
            TraceEventType.OTHER: "批次库存状态已更新",
        }
        return descriptions[event.event_type]


class TraceabilityService:
    """内部追溯查询用例；公开投影使用独立服务。"""

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


__all__ = [
    "PUBLIC_TRACE_DATA_NOTICE",
    "TRACE_READ_PERMISSION",
    "PublicTraceabilityService",
    "TraceEventWriter",
    "TraceabilityCache",
    "TraceabilityService",
]
