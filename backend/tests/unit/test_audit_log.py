from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from app.core.audit.service import AuditEvent, AuditLogService
from app.models import AuditLog, Base
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def audit_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    uuid_defaults = []
    for table in Base.metadata.tables.values():
        id_column = table.c.get("id")
        if id_column is not None and id_column.server_default is not None:
            uuid_defaults.append((id_column, id_column.server_default))
            id_column.server_default = None

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    for column, server_default in uuid_defaults:
        column.server_default = server_default

    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_audit_log_service_persists_redacted_security_event(
    audit_session_factory,
) -> None:
    user_id = uuid4()
    event = AuditEvent(
        action="LOGIN",
        module="AUTH",
        object_type="SESSION",
        result="FAILURE",
        user_id=user_id,
        request_id="req_audit_1",
        ip_address="127.0.0.1",
        user_agent="test-client",
        detail={"reason": "invalid_credentials"},
        created_at=datetime.now(UTC),
    )

    await AuditLogService(audit_session_factory).record(event)

    async with audit_session_factory() as session:
        logs = list((await session.scalars(select(AuditLog))).all())

    assert len(logs) == 1
    assert logs[0].user_id == user_id
    assert logs[0].result == "FAILURE"
    assert logs[0].detail == {"reason": "invalid_credentials"}


@pytest.mark.asyncio
async def test_audit_log_service_rejects_sensitive_detail_fields(
    audit_session_factory,
) -> None:
    event = AuditEvent(
        action="LOGIN",
        module="AUTH",
        object_type="AUTHENTICATION",
        result="FAILURE",
        detail={"refresh_token": "must-not-be-stored"},
    )

    with pytest.raises(ValueError, match="禁止记录"):
        await AuditLogService(audit_session_factory).record(event)
