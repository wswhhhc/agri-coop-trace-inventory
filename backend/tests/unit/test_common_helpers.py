from __future__ import annotations

import pytest
from app.api._pagination import build_pagination_meta
from app.core.exceptions import AppException
from app.core.validation import require_non_empty_update


@pytest.mark.parametrize(
    ("total", "page", "page_size", "expected_pages"),
    [(0, 1, 20, 0), (1, 1, 20, 1), (21, 2, 20, 2)],
)
def test_build_pagination_meta_calculates_total_pages(
    total: int,
    page: int,
    page_size: int,
    expected_pages: int,
) -> None:
    pagination = build_pagination_meta(total, page, page_size)

    assert pagination.page == page
    assert pagination.page_size == page_size
    assert pagination.total_items == total
    assert pagination.total_pages == expected_pages


def test_require_non_empty_update_returns_original_values() -> None:
    values = {"name": "updated"}

    assert require_non_empty_update(values) is values


def test_require_non_empty_update_rejects_empty_values() -> None:
    with pytest.raises(AppException) as error:
        require_non_empty_update({})

    assert error.value.code == "BAD_REQUEST"
    assert error.value.message == "至少提供一个需要更新的字段"
    assert error.value.status_code == 400
