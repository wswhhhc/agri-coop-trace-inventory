from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import BaseSchema


class ReportType(StrEnum):
    INVENTORY_DETAIL = "INVENTORY_DETAIL"
    ALERT_DETAIL = "ALERT_DETAIL"


class ExportFilters(BaseSchema):
    warehouse_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> ExportFilters:
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("结束日期不能早于开始日期")
            if (self.end_date - self.start_date).days + 1 > 366:
                raise ValueError("导出日期范围不能超过366天")
        return self


class ExportTaskCreate(BaseSchema):
    report_type: ReportType
    filters: ExportFilters = Field(default_factory=ExportFilters)


class ExportTaskResult(BaseSchema):
    download_url: str
    expires_at: str
    filename: str


__all__ = ["ExportFilters", "ExportTaskCreate", "ExportTaskResult", "ReportType"]
