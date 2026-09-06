from datetime import UTC, datetime

import pytest
from app.models import Base, TraceEvent, TraceEventType
from app.schemas.traceability import TraceEventCreate
from pydantic import ValidationError
from sqlalchemy import inspect


def test_trace_event_is_registered_as_an_immutable_business_model() -> None:
    assert TraceEvent.__module__ == "app.models.trace_event"
    assert "trace_events" in Base.metadata.tables
    assert "updated_at" not in {column.name for column in inspect(TraceEvent).columns}
    assert inspect(TraceEvent).columns.event_type.type.enum_class is TraceEventType


def test_trace_event_matches_database_contract() -> None:
    assert {
        "id",
        "cooperative_id",
        "batch_id",
        "event_type",
        "title",
        "description",
        "event_time",
        "source_type",
        "source_id",
        "public_data",
        "created_by",
        "created_at",
    } == {column.name for column in inspect(TraceEvent).columns}
    assert {
        constraint.name for constraint in TraceEvent.__table__.constraints
    } >= {"ck_trace_events_type"}
    assert {
        foreign_key.target_fullname
        for foreign_key in TraceEvent.__table__.foreign_keys
    } == {"cooperatives.id", "batches.id", "users.id"}
    assert {index.name for index in TraceEvent.__table__.indexes} == {
        "ix_trace_events_batch_time"
    }


def test_trace_event_payload_rejects_empty_or_oversized_public_fields() -> None:
    with pytest.raises(ValidationError):
        TraceEventCreate(
            event_type=TraceEventType.PRODUCTION,
            title="",
            event_time=datetime.now(UTC),
        )
    with pytest.raises(ValidationError):
        TraceEventCreate(
            event_type=TraceEventType.PRODUCTION,
            title="x" * 101,
            event_time=datetime.now(UTC),
        )
