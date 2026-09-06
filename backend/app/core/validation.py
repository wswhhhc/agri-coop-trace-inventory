from __future__ import annotations

from typing import Any

from app.core.exceptions import AppException


def require_non_empty_update(values: dict[str, Any]) -> dict[str, Any]:
    """确保 PATCH 更新至少包含一个字段，并返回原始字段字典。"""
    if not values:
        raise AppException(
            code="BAD_REQUEST",
            message="至少提供一个需要更新的字段",
            status_code=400,
        )
    return values


__all__ = ["require_non_empty_update"]
