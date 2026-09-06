from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.models import TraceEventType
from app.schemas.traceability import TraceEventListParams
from app.services.traceability import TraceabilityService, TraceEventWriter
from tests.factories import batch_factory

pytestmark = pytest.mark.postgres


def _context(*, user_id, cooperative_id) -> AuthContext:
    return AuthContext(
        user_id=user_id,
        username="trace-admin",
        real_name="追溯管理员",
        role_code="COOPERATIVE_ADMIN",
        permission_codes=frozenset({"trace:read"}),
        cooperative_id=cooperative_id,
        warehouse_ids=frozenset(),
        session_id="trace-session",
        token_id="trace-token",
    )


@pytest.mark.asyncio
async def test_trace_event_writer_appends_and_internal_service_lists_stable_timeline(
    postgres_session,
):
    batch = batch_factory()
    postgres_session.add(batch)
    await postgres_session.flush()
    context = _context(user_id=batch.created_by, cooperative_id=batch.cooperative_id)
    writer = TraceEventWriter(postgres_session)

    first = await writer.record(
        batch=batch,
        event_type=TraceEventType.PRODUCTION,
        title="生产批次建立",
        description="批次信息已登记",
        event_time=datetime(2026, 9, 5, 8, tzinfo=UTC),
        created_by=batch.created_by,
    )
    second = await writer.record(
        batch=batch,
        event_type=TraceEventType.INSPECTION,
        title="质量检验完成",
        event_time=datetime(2026, 9, 5, 9, tzinfo=UTC),
        created_by=batch.created_by,
    )
    await postgres_session.commit()

    service = TraceabilityService(postgres_session)
    items, total = await service.list_internal(
        context,
        batch.id,
        TraceEventListParams(page=1, page_size=10),
    )

    assert total == 2
    assert [item.id for item in items] == [first.id, second.id]
    assert [item.event_type for item in items] == [
        TraceEventType.PRODUCTION,
        TraceEventType.INSPECTION,
    ]


@pytest.mark.asyncio
async def test_internal_trace_query_hides_batch_outside_auth_scope(postgres_session):
    batch = batch_factory()
    postgres_session.add(batch)
    await postgres_session.flush()
    await postgres_session.commit()
    context = _context(user_id=batch.created_by, cooperative_id=uuid4())

    service = TraceabilityService(postgres_session)

    with pytest.raises(AppException) as error:
        await service.list_internal(context, batch.id, TraceEventListParams())

    assert getattr(error.value, "status_code", None) == 404
