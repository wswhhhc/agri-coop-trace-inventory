from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, Uuid, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models._common import utc_now
from app.models.base import Base

_IP_ADDRESS_TYPE = INET().with_variant(String(45), "sqlite")
_DETAIL_TYPE = JSONB().with_variant(JSON, "sqlite")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "result IN ('SUCCESS', 'FAILURE')", name="ck_audit_logs_result"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cooperative_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    module: Mapped[str] = mapped_column(String(32), nullable=False)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    result: Mapped[str] = mapped_column(String(16), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64))
    ip_address: Mapped[str | None] = mapped_column(_IP_ADDRESS_TYPE)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    detail: Mapped[dict[str, Any]] = mapped_column(
        _DETAIL_TYPE,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )


__all__ = ["AuditLog"]
