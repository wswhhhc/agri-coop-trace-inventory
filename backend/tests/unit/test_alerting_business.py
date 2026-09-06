from uuid import uuid4

import pytest
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.models import AlertSeverity, AlertStatus, AlertType
from app.schemas.alerting import AlertListParams
from app.services.alerting import allowed_status_transitions
from app.services.alerting_policy import (
    require_alert_handle,
    require_alert_read,
    require_rule_manage,
)


def _context(*, role_code: str, permissions: set[str]) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="alert-user",
        real_name="预警用户",
        role_code=role_code,
        permission_codes=frozenset(permissions),
        cooperative_id=uuid4(),
        warehouse_ids=frozenset({uuid4()}),
        session_id="session",
        token_id="token",
    )


def test_alert_status_transitions_follow_contract() -> None:
    assert allowed_status_transitions(AlertStatus.PENDING) == {
        AlertStatus.PROCESSING,
        AlertStatus.RESOLVED,
        AlertStatus.IGNORED,
    }
    assert allowed_status_transitions(AlertStatus.PROCESSING) == {
        AlertStatus.RESOLVED,
        AlertStatus.IGNORED,
    }
    assert allowed_status_transitions(AlertStatus.RESOLVED) == set()
    assert allowed_status_transitions(AlertStatus.IGNORED) == set()


def test_alerting_permissions_match_role_contract() -> None:
    require_alert_read(_context(role_code="WAREHOUSE_STAFF", permissions={"alert:read"}))
    require_alert_handle(_context(role_code="WAREHOUSE_STAFF", permissions={"alert:handle"}))
    require_rule_manage(_context(role_code="COOPERATIVE_ADMIN", permissions={"alert:read"}))

    with pytest.raises(AppException) as error:
        require_alert_handle(_context(role_code="WAREHOUSE_STAFF", permissions=set()))
    assert error.value.status_code == 403

    with pytest.raises(AppException) as error:
        require_rule_manage(_context(role_code="WAREHOUSE_STAFF", permissions={"alert:read"}))
    assert error.value.status_code == 403


def test_alerting_schemas_accept_camel_case_filters_and_reject_invalid_time_range() -> None:
    params = AlertListParams(
        type=AlertType.NEAR_EXPIRY,
        severity=AlertSeverity.MEDIUM,
        createdAfter="2026-09-01T00:00:00Z",
        createdBefore="2026-09-02T00:00:00Z",
    )
    assert params.created_after is not None
    assert params.created_before is not None

    with pytest.raises(ValueError):
        AlertListParams(
            createdAfter="2026-09-03T00:00:00Z",
            createdBefore="2026-09-02T00:00:00Z",
        )


def test_alerting_router_is_registered() -> None:
    from app.main import create_app

    paths = set(create_app().openapi()["paths"])
    assert "/api/v1/alert-rules" in paths
    assert "/api/v1/alert-rules/{ruleId}" in paths
    assert "/api/v1/alerts" in paths
    assert "/api/v1/alerts/{alertId}" in paths
    assert "/api/v1/alert-scan-tasks" in paths
