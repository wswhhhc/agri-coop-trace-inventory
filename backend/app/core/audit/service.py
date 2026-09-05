from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.audit.context import AuditContext
from app.models._common import utc_now
from app.repositories.audit_log import AuditLogRepository

_FORBIDDEN_DETAIL_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "cookie",
    "set-cookie",
}


@dataclass(frozen=True, slots=True)
class AuditEvent:
    action: str
    module: str
    object_type: str
    result: str
    cooperative_id: UUID | None = None
    user_id: UUID | None = None
    object_id: UUID | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    @classmethod
    def from_context(
        cls,
        *,
        context: AuditContext | None,
        action: str,
        object_type: str,
        result: str,
        cooperative_id: UUID | None = None,
        user_id: UUID | None = None,
        object_id: UUID | None = None,
        detail: dict[str, Any] | None = None,
    ) -> AuditEvent:
        return cls(
            action=action,
            module="AUTH",
            object_type=object_type,
            result=result,
            cooperative_id=cooperative_id,
            user_id=user_id,
            object_id=object_id,
            request_id=context.request_id if context else None,
            ip_address=context.ip_address if context else None,
            user_agent=context.user_agent if context else None,
            detail=dict(detail or {}),
            created_at=datetime.now(UTC),
        )


class AuditLogService:
    """使用独立事务持久化安全审计事件。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def record(self, event: AuditEvent) -> None:
        _validate_detail(event.detail)
        async with self.session_factory() as session, session.begin():
            await AuditLogRepository(session).create(event)


def _validate_detail(detail: dict[str, Any]) -> None:
    forbidden = set(_iter_forbidden_detail_keys(detail))
    if forbidden:
        raise ValueError(f"审计详情包含禁止记录的字段: {', '.join(sorted(forbidden))}")


def _iter_forbidden_detail_keys(value: Any):
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = str(key).lower()
            if normalized_key in _FORBIDDEN_DETAIL_KEYS:
                yield normalized_key
            yield from _iter_forbidden_detail_keys(nested_value)
    elif isinstance(value, (list, tuple)):
        for nested_value in value:
            yield from _iter_forbidden_detail_keys(nested_value)


__all__ = ["AuditEvent", "AuditLogService"]
