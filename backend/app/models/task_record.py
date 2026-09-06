from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TaskStatus, enum_sql_values

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.user import User


class TaskRecord(Base):
    __tablename__ = "task_records"
    __table_args__ = (
        CheckConstraint(f"status IN ({enum_sql_values(TaskStatus)})", name="ck_task_records_status"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="ck_task_records_progress"),
        CheckConstraint("finished_at IS NULL OR started_at IS NOT NULL", name="ck_task_records_time_order_presence"),
        CheckConstraint("finished_at IS NULL OR finished_at >= started_at", name="ck_task_records_time_order"),
        UniqueConstraint("celery_task_id", name="uq_task_records_celery_id"),
        Index("ix_task_records_cooperative_created", "cooperative_id", text("created_at DESC")),
    )

    cooperative_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("cooperatives.id", ondelete="RESTRICT"))
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    celery_task_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        SqlEnum(TaskStatus, native_enum=False, create_constraint=False, name="ck_task_records_status", length=16),
        nullable=False, default=TaskStatus.PENDING, server_default=TaskStatus.PENDING.value,
    )
    progress: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default="0")
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(500))
    requested_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    cooperative: Mapped[Cooperative | None] = relationship("Cooperative")
    requester: Mapped[User | None] = relationship("User")


__all__ = ["TaskRecord"]
