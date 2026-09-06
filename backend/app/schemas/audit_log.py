from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from app.schemas.common import BaseSchema, PageParams


class AuditLogListParams(PageParams):
    user_id: UUID | None = None
    action: str | None = Field(default=None, min_length=1, max_length=64)
    resource_type: str | None = Field(default=None, min_length=1, max_length=64)
    resource_id: UUID | None = None
    result: Literal["SUCCESS", "FAILURE"] | None = None
    start_date: AwareDatetime | None = None
    end_date: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> AuditLogListParams:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date 不能早于 start_date")
        return self


class AuditLogData(BaseSchema):
    id: UUID
    cooperative_id: UUID | None
    user_id: UUID | None
    action: str
    module: str
    resource_type: str
    resource_id: UUID | None
    result: Literal["SUCCESS", "FAILURE"]
    request_id: str | None
    detail: dict[str, Any]
    created_at: datetime


__all__ = ["AuditLogData", "AuditLogListParams"]
