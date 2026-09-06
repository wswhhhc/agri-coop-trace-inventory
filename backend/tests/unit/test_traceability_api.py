from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.api.traceability import _trace_event_data, router
from app.main import create_app
from app.models import TraceEventType


def test_traceability_router_owns_internal_trace_event_endpoint() -> None:
    routes = {(route.path, tuple(sorted(route.methods or set()))) for route in router.routes}

    assert ("/batches/{batchId}/trace-events", ("GET",)) in routes


def test_traceability_routes_are_registered_in_api_v1() -> None:
    paths = set(create_app().openapi()["paths"])

    assert "/api/v1/batches/{batchId}/trace-events" in paths


def test_trace_event_response_maps_internal_event_fields() -> None:
    event = SimpleNamespace(
        id=uuid4(),
        cooperative_id=uuid4(),
        batch_id=uuid4(),
        event_type=TraceEventType.PRODUCTION,
        title="生产批次建立",
        description="批次信息已登记",
        event_time=datetime(2026, 9, 5, 8, tzinfo=UTC),
        source_type=None,
        source_id=None,
        public_data={},
        created_by=uuid4(),
        created_at=datetime(2026, 9, 5, 8, tzinfo=UTC),
    )

    data = _trace_event_data(event)

    assert data.event_type is TraceEventType.PRODUCTION
    assert data.title == "生产批次建立"
