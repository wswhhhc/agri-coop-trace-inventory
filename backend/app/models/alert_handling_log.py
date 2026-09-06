from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Uuid
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AlertStatus, enum_sql_values

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.user import User


class AlertHandlingLog(Base):
    __tablename__ = "alert_handling_logs"
    __table_args__ = (
        CheckConstraint(
            f"from_status IN ({enum_sql_values(AlertStatus)})",
            name="ck_alert_handling_logs_from_status",
        ),
        CheckConstraint(
            f"to_status IN ({enum_sql_values(AlertStatus)})",
            name="ck_alert_handling_logs_to_status",
        ),
        Index("ix_alert_handling_logs_alert_time", "alert_id", "created_at"),
    )

    updated_at = None  # type: ignore[assignment]

    alert_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("alerts.id", ondelete="RESTRICT"), nullable=False
    )
    operator_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    from_status: Mapped[AlertStatus] = mapped_column(
        SqlEnum(AlertStatus, native_enum=False, create_constraint=False, name="ck_alert_handling_logs_from_status", length=16), nullable=False
    )
    to_status: Mapped[AlertStatus] = mapped_column(
        SqlEnum(AlertStatus, native_enum=False, create_constraint=False, name="ck_alert_handling_logs_to_status", length=16), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(String(500))

    alert: Mapped[Alert] = relationship("Alert", back_populates="handling_logs")
    operator: Mapped[User] = relationship("User")


__all__ = ["AlertHandlingLog"]
