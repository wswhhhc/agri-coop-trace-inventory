from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.common import (
    ApiResponse,
    ErrorResponse,
    ListResponse,
    PageParams,
    PaginationMeta,
    ResourceMeta,
    SortOrder,
)


def test_base_schema_accepts_python_names_and_serializes_camel_case() -> None:
    resource_id = uuid4()
    resource = ResourceMeta(
        id=resource_id,
        created_at=datetime(2026, 9, 5, 8, 30, tzinfo=UTC),
        updated_at=datetime(2026, 9, 5, 8, 30, tzinfo=UTC),
    )

    assert resource.model_dump(by_alias=True) == {
        "id": resource_id,
        "createdAt": datetime(2026, 9, 5, 8, 30, tzinfo=UTC),
        "updatedAt": datetime(2026, 9, 5, 8, 30, tzinfo=UTC),
        "createdBy": None,
    }


def test_resource_schema_reads_orm_attributes_and_aliases() -> None:
    resource_id = uuid4()
    resource = ResourceMeta.model_validate(
        SimpleNamespace(
            id=resource_id,
            created_at=datetime(2026, 9, 5, 8, 30, tzinfo=UTC),
            updated_at=datetime(2026, 9, 5, 8, 30, tzinfo=UTC),
            created_by=None,
        )
    )

    assert resource.id == resource_id


def test_page_params_use_contract_defaults_and_validate_bounds() -> None:
    params = PageParams()

    assert params.page == 1
    assert params.page_size == 20
    assert params.sort_by == "createdAt"
    assert params.sort_order is SortOrder.DESC
    assert params.model_dump(by_alias=True)["pageSize"] == 20

    with pytest.raises(ValidationError):
        PageParams(page=0)
    with pytest.raises(ValidationError):
        PageParams(page_size=101)


def test_page_params_reject_unknown_query_fields() -> None:
    with pytest.raises(ValidationError):
        PageParams(unknownField="unexpected")


def test_response_envelopes_serialize_data_and_pagination() -> None:
    pagination = PaginationMeta(page=1, page_size=20, total_items=1, total_pages=1)
    response = ListResponse[str](data=["ok"], pagination=pagination)

    assert response.model_dump(by_alias=True) == {
        "data": ["ok"],
        "pagination": {
            "page": 1,
            "pageSize": 20,
            "totalItems": 1,
            "totalPages": 1,
        },
    }
    assert ApiResponse[str](data="ok").data == "ok"


def test_pagination_rejects_negative_totals() -> None:
    with pytest.raises(ValidationError):
        PaginationMeta(page=1, page_size=20, total_items=-1, total_pages=0)


def test_error_response_uses_public_error_contract() -> None:
    response = ErrorResponse(
        error={
            "code": "VALIDATION_ERROR",
            "message": "请求字段校验失败",
            "details": {"field": "pageSize"},
            "request_id": "req_123",
        }
    )

    assert response.model_dump(by_alias=True) == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "请求字段校验失败",
            "details": {"field": "pageSize"},
            "requestId": "req_123",
        }
    }
