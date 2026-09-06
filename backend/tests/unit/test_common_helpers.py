from __future__ import annotations

import pytest
from app.api._pagination import build_pagination_meta
from app.core.exceptions import AppException
from app.core.validation import require_non_empty_update
from app.repositories._query_helpers import contains_pattern
from app.utils.crypto import sha256_hex


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


@pytest.mark.parametrize("value", ["农业", "农业".encode()])
def test_sha256_hex_uses_utf8_for_strings(value: str | bytes) -> None:
    assert sha256_hex(value) == (
        "b2acdef8f2efe1fb86dd8a57b399f7c75cc5fa118b6168eba09d8e4a1070b3d1"
    )


@pytest.mark.parametrize(
    ("keyword", "expected"), [("  apple ", "%apple%"), ("   ", "%%")]
)
def test_contains_pattern_preserves_current_like_behavior(
    keyword: str, expected: str
) -> None:
    assert contains_pattern(keyword) == expected
