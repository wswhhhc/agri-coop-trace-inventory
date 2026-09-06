from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, Field, field_validator, model_validator

from app.models.enums import AlertSeverity, AlertStatus, AlertType
from app.schemas.common import BaseSchema, PageParams


class AlertRuleUpdate(BaseSchema):
    threshold_quantity: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=3)
    threshold_days: int | None = Field(default=None, ge=0)
    turnover_days: int | None = Field(default=None, ge=0)
    severity: AlertSeverity | None = None
    is_enabled: bool | None = None

    @model_validator(mode="after")
    def require_value(self) -> AlertRuleUpdate:
        if not self.model_fields_set:
            raise ValueError("至少提供一个规则字段")
        return self


class AlertListParams(PageParams):
    type: AlertType | None = None
    severity: AlertSeverity | None = None
    status: AlertStatus | None = None
    warehouse_id: UUID | None = None
    product_id: UUID | None = None
    batch_id: UUID | None = None
    created_after: AwareDatetime | None = None
    created_before: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_time_order(self) -> AlertListParams:
        if self.created_after and self.created_before and self.created_before < self.created_after:
            raise ValueError("createdBefore 不能早于 createdAfter")
        return self


class AlertStatusUpdate(BaseSchema):
    status: AlertStatus
    handling_note: str | None = Field(default=None, max_length=500)

    @field_validator("handling_note")
    @classmethod
    def trim_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("处理说明不能为空")
        return value


class AlertRuleData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    warehouse_id: UUID | None
    product_id: UUID | None
    alert_type: AlertType
    threshold_quantity: Decimal | None
    threshold_days: int | None
    turnover_days: int | None
    severity: AlertSeverity
    is_enabled: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AlertData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    rule_id: UUID | None
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    warehouse_id: UUID | None
    product_id: UUID | None
    batch_id: UUID | None
    title: str
    message: str
    evidence: dict[str, Any]
    detected_at: AwareDatetime
    resolved_at: AwareDatetime | None
    assignee_id: UUID | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    handling_logs: list[dict[str, Any]] = Field(default_factory=list)


__all__ = [
    "AlertData",
    "AlertListParams",
    "AlertRuleData",
    "AlertRuleUpdate",
    "AlertStatusUpdate",
]
