from datetime import UTC, datetime
from decimal import Decimal
from inspect import isclass
from uuid import uuid4

import pytest
from app.models import (
    Alert,
    AlertHandlingLog,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    AlertType,
    Base,
)
from app.schemas.alerting import AlertRuleUpdate, AlertStatusUpdate
from pydantic import ValidationError
from sqlalchemy import inspect


def test_alerting_models_are_registered_and_match_database_shape() -> None:
    assert isclass(AlertRule)
    assert isclass(Alert)
    assert isclass(AlertHandlingLog)
    assert {"alert_rules", "alerts", "alert_handling_logs"}.issubset(
        Base.metadata.tables
    )
    assert {
        "id", "cooperative_id", "warehouse_id", "product_id", "alert_type",
        "threshold_quantity", "threshold_days", "turnover_days", "severity",
        "is_enabled", "created_at", "updated_at",
    } == {column.name for column in inspect(AlertRule).columns}
    assert {
        "id", "cooperative_id", "rule_id", "alert_type", "severity", "status",
        "warehouse_id", "product_id", "batch_id", "dedupe_key", "title", "message",
        "evidence", "detected_at", "resolved_at", "assignee_id", "created_at", "updated_at",
    } == {column.name for column in inspect(Alert).columns}
    assert {
        "id", "alert_id", "operator_id", "from_status", "to_status", "comment", "created_at",
    } == {column.name for column in inspect(AlertHandlingLog).columns}
    assert inspect(AlertRule).columns.alert_type.type.enum_class is AlertType  # type: ignore[attr-defined]
    assert inspect(Alert).columns.status.type.enum_class is AlertStatus  # type: ignore[attr-defined]


def test_alerting_schema_validates_thresholds_and_status_updates() -> None:
    payload = AlertRuleUpdate(
        threshold_quantity=Decimal("10.500"),
        threshold_days=3,
        turnover_days=10,
        severity=AlertSeverity.HIGH,
        is_enabled=True,
    )
    assert payload.threshold_quantity == Decimal("10.500")
    assert payload.model_dump(by_alias=True, exclude_unset=True)["isEnabled"] is True

    status = AlertStatusUpdate(status=AlertStatus.RESOLVED, handling_note="已补货")
    assert status.model_dump(by_alias=True)["handlingNote"] == "已补货"

    with pytest.raises(ValidationError):
        AlertRuleUpdate(threshold_days=-1)
    with pytest.raises(ValidationError):
        AlertStatusUpdate(status=AlertStatus.PROCESSING, handling_note=" ")


def test_alert_model_has_expected_defaults() -> None:
    Alert(
        cooperative_id=uuid4(),
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.HIGH,
        dedupe_key="LOW_STOCK:warehouse:batch:202609",
        title="库存不足",
        message="库存低于安全库存",
        detected_at=datetime.now(UTC),
    )
    assert Alert.__table__.c.status.default.arg is AlertStatus.PENDING
    assert callable(Alert.__table__.c.evidence.default.arg)
