from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid, text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TraceEventType, enum_sql_values

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.cooperative import Cooperative
    from app.models.user import User


class TraceEvent(Base):
    """批次追溯事件；事件历史只允许追加，不提供更新和删除。"""

    __tablename__ = "trace_events"
    __table_args__ = (
        CheckConstraint(
            f"event_type IN ({enum_sql_values(TraceEventType)})",
            name="ck_trace_events_type",
        ),
        Index("ix_trace_events_batch_time", "batch_id", "event_time", "id"),
    )

    updated_at = None  # type: ignore[assignment]

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type: Mapped[TraceEventType] = mapped_column(
        SqlEnum(
            TraceEventType,
            native_enum=False,
            create_constraint=False,
            name="ck_trace_events_type",
            length=32,
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    source_type: Mapped[str | None] = mapped_column(String(32))
    source_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    public_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    cooperative: Mapped[Cooperative] = relationship(
        "Cooperative", back_populates="trace_events"
    )
    batch: Mapped[Batch] = relationship("Batch", back_populates="trace_events")
    creator: Mapped[User | None] = relationship(
        "User", back_populates="trace_events"
    )


__all__ = ["TraceEvent"]
