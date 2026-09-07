from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from app.models.enums import BatchStatus
from app.schemas.common import BaseSchema, PageParams


class BatchCreate(BaseSchema):
    product_id: UUID
    origin: str = Field(min_length=1, max_length=255)
    production_date: date
    expiry_date: date
    responsible_person: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def validate_date_order(self) -> BatchCreate:
        if self.expiry_date < self.production_date:
            raise ValueError("expiry_date 不能早于 production_date")
        return self


class BatchUpdate(BaseSchema):
    origin: str | None = Field(default=None, min_length=1, max_length=255)
    expiry_date: date | None = None
    responsible_person: str | None = Field(default=None, max_length=50)
    status: BatchStatus | None = None


class BatchListParams(PageParams):
    keyword: str | None = Field(default=None, max_length=100)
    product_id: UUID | None = None
    warehouse_id: UUID | None = None
    status: BatchStatus | None = None
    production_date_from: date | None = None
    production_date_to: date | None = None


class BatchData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    product_id: UUID
    batch_no: str
    trace_code: str
    origin: str
    production_date: date
    expiry_date: date
    responsible_person: str | None
    status: BatchStatus
    created_by: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


__all__ = ["BatchCreate", "BatchData", "BatchListParams", "BatchUpdate"]
