from __future__ import annotations

from typing import Any

FORBIDDEN_DETAIL_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "cookie",
        "set-cookie",
    }
)
REDACTED_VALUE = "[REDACTED]"


def iter_sensitive_detail_keys(value: Any):
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = str(key).lower()
            if normalized_key in FORBIDDEN_DETAIL_KEYS:
                yield normalized_key
            yield from iter_sensitive_detail_keys(nested_value)
    elif isinstance(value, (list, tuple)):
        for nested_value in value:
            yield from iter_sensitive_detail_keys(nested_value)


def redact_detail(value: Any) -> Any:
    """返回可安全展示的审计上下文，不修改已持久化的原始值。"""
    if isinstance(value, dict):
        return {
            str(key): (
                REDACTED_VALUE
                if str(key).lower() in FORBIDDEN_DETAIL_KEYS
                else redact_detail(nested_value)
            )
            for key, nested_value in value.items()
        }
    if isinstance(value, list):
        return [redact_detail(item) for item in value]
    if isinstance(value, tuple):
        return [redact_detail(item) for item in value]
    return value


__all__ = [
    "FORBIDDEN_DETAIL_KEYS",
    "REDACTED_VALUE",
    "iter_sensitive_detail_keys",
    "redact_detail",
]
