from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, Field

from app.models.enums import BatchStatus, InspectionConclusion, TraceEventType
from app.schemas.common import BaseSchema, PageParams, SortOrder


class TraceEventCreate(BaseSchema):
    """追溯事件写入契约；批次和创建人由服务端上下文确定。"""

    event_type: TraceEventType
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    event_time: AwareDatetime
    source_type: str | None = Field(default=None, min_length=1, max_length=32)
    source_id: UUID | None = None
    public_data: dict[str, Any] = Field(default_factory=dict)


class TraceEventListParams(PageParams):
    event_type: TraceEventType | None = None
    sort_by: str = Field(default="eventTime", min_length=1, max_length=50)
    sort_order: SortOrder = SortOrder.ASC


class TraceEventData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    batch_id: UUID
    event_type: TraceEventType
    title: str
    description: str | None
    event_time: AwareDatetime
    source_type: str | None
    source_id: UUID | None
    public_data: dict[str, Any]
    created_by: UUID | None
    created_at: AwareDatetime


class PublicTraceProductData(BaseSchema):
    name: str
    category_name: str
    unit: str
    description: str | None = None


class PublicTraceBatchData(BaseSchema):
    batch_no: str
    origin: str
    production_date: date
    expiry_date: date
    status: BatchStatus


class PublicTraceInspectionItemData(BaseSchema):
    name: str
    value: str
    unit: str | None
    standard: str
    is_qualified: bool


class PublicTraceInspectionData(BaseSchema):
    inspection_date: date
    conclusion: InspectionConclusion
    items: list[PublicTraceInspectionItemData]


class PublicTraceTimelineEventData(BaseSchema):
    event_type: TraceEventType
    title: str
    description: str
    occurred_at: AwareDatetime


class PublicTraceData(BaseSchema):
    trace_code: str
    product: PublicTraceProductData
    batch: PublicTraceBatchData
    latest_inspection: PublicTraceInspectionData | None
    timeline: list[PublicTraceTimelineEventData]
    data_notice: str
    updated_at: AwareDatetime


__all__ = [
    "PublicTraceBatchData",
    "PublicTraceData",
    "PublicTraceInspectionData",
    "PublicTraceInspectionItemData",
    "PublicTraceProductData",
    "PublicTraceTimelineEventData",
    "TraceEventCreate",
    "TraceEventData",
    "TraceEventListParams",
]
