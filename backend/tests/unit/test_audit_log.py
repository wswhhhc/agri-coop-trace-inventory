from __future__ import annotations

import logging
from datetime import UTC, datetime

import pytest
from app.core.audit.service import (
    AuditEvent,
    AuditLogService,
    record_audit_safely,
)
from app.models import AuditLog
from sqlalchemy import select
from tests.factories import user_factory


class _FailingAuditService:
    async def record(self, event: AuditEvent) -> None:
        raise RuntimeError("audit backend unavailable")


@pytest.mark.asyncio
async def test_audit_log_service_persists_redacted_security_event(
    postgres_session_factory,
) -> None:
    user = user_factory()
    async with postgres_session_factory() as session:
        session.add(user)
        await session.commit()

    event = AuditEvent(
        action="LOGIN",
        module="AUTH",
        object_type="SESSION",
        result="FAILURE",
        user_id=user.id,
        cooperative_id=user.cooperative_id,
        request_id="req_audit_1",
        ip_address="127.0.0.1",
        user_agent="test-client",
        detail={"reason": "invalid_credentials"},
        created_at=datetime.now(UTC),
    )

    await AuditLogService(postgres_session_factory).record(event)

    async with postgres_session_factory() as session:
        logs = list((await session.scalars(select(AuditLog))).all())

    assert len(logs) == 1
    assert logs[0].user_id == user.id
    assert logs[0].result == "FAILURE"
    assert logs[0].detail == {"reason": "invalid_credentials"}


@pytest.mark.asyncio
async def test_audit_log_service_rejects_sensitive_detail_fields(
    postgres_session_factory,
) -> None:
    event = AuditEvent(
        action="LOGIN",
        module="AUTH",
        object_type="AUTHENTICATION",
        result="FAILURE",
        detail={"refresh_token": "must-not-be-stored"},
    )

    with pytest.raises(ValueError, match="禁止记录"):
        await AuditLogService(postgres_session_factory).record(event)


@pytest.mark.asyncio
async def test_audit_log_service_rejects_nested_sensitive_detail_fields(
    postgres_session_factory,
) -> None:
    event = AuditEvent(
        action="LOGIN",
        module="AUTH",
        object_type="AUTHENTICATION",
        result="FAILURE",
        detail={"metadata": [{"access_token": "must-not-be-stored"}]},
    )

    with pytest.raises(ValueError, match="禁止记录"):
        await AuditLogService(postgres_session_factory).record(event)


@pytest.mark.asyncio
async def test_record_audit_safely_does_not_break_business_on_audit_failure(
    caplog,
) -> None:
    with caplog.at_level(logging.ERROR):
        await record_audit_safely(
            _FailingAuditService(),
            AuditEvent(
                action="CREATE_BATCH",
                module="BATCH",
                object_type="BATCH",
                result="SUCCESS",
            ),
            logging.getLogger("test.audit"),
        )

    assert "审计记录失败 action=CREATE_BATCH" in caplog.text
