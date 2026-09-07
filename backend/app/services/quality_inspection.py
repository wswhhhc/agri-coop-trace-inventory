from __future__ import annotations

from datetime import UTC, datetime, time
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import resource_not_found
from app.core.auth.context import AuthContext
from app.infrastructure.transaction import transaction_scope
from app.models import (
    Batch,
    InspectionFile,
    QualityInspection,
    QualityInspectionItem,
    TraceEventType,
)
from app.repositories.batch import BatchRepository
from app.repositories.file import FileRepository
from app.repositories.quality_inspection import QualityInspectionRepository
from app.schemas.quality_inspection import (
    QualityInspectionCreate,
    QualityInspectionListParams,
)
from app.services.batch_policy import (
    require_manage,
    require_read_role,
    warehouse_ids_for_query,
)
from app.services.traceability import TraceabilityCache, TraceEventWriter


class QualityIntegrationPort(Protocol):
    """质检向追溯和预警模块暴露的最小对接端口。"""

    async def inspection_created(self, inspection: QualityInspection) -> None: ...

    async def quality_failed(self, inspection: QualityInspection) -> None: ...


class NullQualityIntegration:
    """下游模块尚未接入时的安全默认实现。"""

    async def inspection_created(self, inspection: QualityInspection) -> None:
        return None

    async def quality_failed(self, inspection: QualityInspection) -> None:
        return None


class QualityInspectionService:
    """质检新增和查询用例；历史记录只允许追加，不提供更新/删除。"""

    def __init__(
        self,
        session: AsyncSession,
        integration: QualityIntegrationPort | None = None,
        cache: TraceabilityCache | None = None,
    ) -> None:
        self.session = session
        self.repository = QualityInspectionRepository(session)
        self.batch_repository = BatchRepository(session)
        self.file_repository = FileRepository(session)
        self.trace_writer = TraceEventWriter(session)
        self.trace_cache = cache
        self.integration = integration or NullQualityIntegration()

    @staticmethod
    def ensure_read_access(context: AuthContext) -> None:
        require_read_role(context)

    async def list(
        self,
        context: AuthContext,
        batch_id: UUID,
        params: QualityInspectionListParams | None = None,
    ) -> tuple[list[QualityInspection], int]:
        require_read_role(context)
        params = params or QualityInspectionListParams()
        async with transaction_scope(self.session):
            batch = await self._get_batch(context, batch_id)
            if batch is None:
                raise resource_not_found()
            return await self.repository.list_scoped(
                context.cooperative_id,
                batch.id,
                conclusion=params.conclusion,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )

    async def create(
        self,
        context: AuthContext,
        batch_id: UUID,
        payload: QualityInspectionCreate,
    ) -> QualityInspection:
        require_manage(context)
        async with transaction_scope(self.session):
            batch = await self._get_batch(context, batch_id)
            if batch is None:
                raise resource_not_found()
            if payload.original_inspection_id is not None:
                original = await self.repository.get_scoped(
                    context.cooperative_id,
                    batch.id,
                    payload.original_inspection_id,
                )
                if original is None:
                    raise resource_not_found()
            files = await self.file_repository.list_scoped(
                batch.cooperative_id, payload.attachment_file_ids
            )
            if len(files) != len(set(payload.attachment_file_ids)):
                raise resource_not_found()

            inspection = QualityInspection(
                cooperative_id=batch.cooperative_id,
                batch_id=batch.id,
                inspection_no=self._new_inspection_no(payload.inspection_date),
                inspected_at=datetime.combine(
                    payload.inspection_date, time.min, tzinfo=UTC
                ),
                inspector_id=context.user_id,
                conclusion=payload.conclusion,
                remarks=payload.remarks,
                original_inspection_id=payload.original_inspection_id,
                items=[
                    QualityInspectionItem(
                        item_name=item.item_name,
                        unit=item.unit,
                        standard_value=item.standard_value,
                        result_value=item.result_value,
                        is_qualified=item.is_qualified,
                        sort_order=index,
                    )
                    for index, item in enumerate(payload.items)
                ],
            )
            inspection.file_links = [
                InspectionFile(file_id=file.id) for file in files
            ]
            created = await self.repository.add(inspection)
            await self.trace_writer.record(
                batch=batch,
                event_type=TraceEventType.INSPECTION,
                title="质量检验完成",
                description=f"检验结论：{created.conclusion.value}",
                event_time=created.inspected_at,
                source_type="QUALITY_INSPECTION",
                source_id=created.id,
                public_data=self._public_inspection_data(created),
                created_by=context.user_id,
            )
            await self.integration.inspection_created(created)
            if created.conclusion.value == "FAILED":
                await self.integration.quality_failed(created)
        await self._invalidate_trace_cache(batch.trace_code)
        return created

    async def _invalidate_trace_cache(self, trace_code: str) -> None:
        if self.trace_cache is not None:
            await self.trace_cache.invalidate(trace_code)

    @staticmethod
    def _public_inspection_data(inspection: QualityInspection) -> dict[str, object]:
        return {
            "inspectionDate": inspection.inspected_at.date().isoformat(),
            "conclusion": inspection.conclusion.value,
            "items": [
                {
                    "name": item.item_name,
                    "value": item.result_value,
                    "unit": item.unit,
                    "standard": item.standard_value,
                    "isQualified": item.is_qualified,
                }
                for item in inspection.items
            ],
        }

    async def _get_batch(
        self, context: AuthContext, batch_id: UUID
    ) -> Batch | None:
        return await self.batch_repository.get_scoped(
            context.cooperative_id,
            warehouse_ids_for_query(context),
            batch_id,
        )

    @staticmethod
    def _new_inspection_no(inspection_date) -> str:
        return f"QC-{inspection_date:%Y%m%d}-{uuid4().hex[:10].upper()}"

__all__ = [
    "NullQualityIntegration",
    "QualityInspectionService",
    "QualityIntegrationPort",
]
