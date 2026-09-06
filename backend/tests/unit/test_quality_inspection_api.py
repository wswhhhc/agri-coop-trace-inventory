from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.api.files import router as files_router
from app.api.quality_inspections import _quality_inspection_data, router
from app.main import create_app
from app.models import InspectionConclusion


def test_quality_router_owns_only_quality_inspection_endpoints() -> None:
    routes = {(route.path, tuple(sorted(route.methods or set()))) for route in router.routes}

    assert (
        "/batches/{batchId}/quality-inspections",
        ("GET",),
    ) in routes
    assert (
        "/batches/{batchId}/quality-inspections",
        ("POST",),
    ) in routes
    assert all("users" not in route.path and "files" not in route.path for route in router.routes)


def test_file_router_owns_only_file_endpoints() -> None:
    routes = {(route.path, tuple(sorted(route.methods or set()))) for route in files_router.routes}

    assert ("/files", ("POST",)) in routes
    assert ("/files/{fileId}", ("GET",)) in routes
    assert all("users" not in route.path and "quality" not in route.path for route in files_router.routes)


def test_quality_routes_are_registered_in_api_v1() -> None:
    application = create_app()
    paths = set(application.openapi()["paths"])

    assert "/api/v1/batches/{batchId}/quality-inspections" in paths
    assert "/api/v1/files" in paths
    assert "/api/v1/files/{fileId}" in paths


def test_quality_response_maps_nested_records_without_leaking_storage_paths() -> None:
    inspection_id = uuid4()
    file_id = uuid4()
    inspection = SimpleNamespace(
        id=inspection_id,
        cooperative_id=uuid4(),
        batch_id=uuid4(),
        inspection_no="QC-20260905-ABC",
        inspected_at=datetime(2026, 9, 5, tzinfo=UTC),
        inspector_id=uuid4(),
        inspector=SimpleNamespace(real_name="王某"),
        conclusion=InspectionConclusion.PASSED,
        remarks=None,
        original_inspection_id=None,
        items=[
            SimpleNamespace(
                id=uuid4(),
                item_name="水分",
                result_value="13.2",
                unit="%",
                standard_value="≤14",
                is_qualified=True,
                sort_order=0,
            )
        ],
        file_links=[SimpleNamespace(file_id=file_id)],
        created_at=datetime(2026, 9, 5, tzinfo=UTC),
        updated_at=datetime(2026, 9, 5, tzinfo=UTC),
    )

    data = _quality_inspection_data(inspection)

    assert data.inspection_date == date(2026, 9, 5)
    assert data.inspector_name == "王某"
    assert data.items[0].name == "水分"
    assert data.attachment_file_ids == [file_id]
    assert "storage" not in data.model_dump_json()
