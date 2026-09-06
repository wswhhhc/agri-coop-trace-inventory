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
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import IdempotencyStatus, enum_sql_values

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.user import User


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({enum_sql_values(IdempotencyStatus)})",
            name="ck_idempotency_records_status",
        ),
        CheckConstraint(
            "response_status IS NULL OR response_status BETWEEN 100 AND 599",
            name="ck_idempotency_records_response_status",
        ),
        CheckConstraint(
            "expires_at > created_at", name="ck_idempotency_records_expiry"
        ),
        UniqueConstraint(
            "user_id", "endpoint", "idempotency_key", name="uq_idempotency_records_request"
        ),
        Index("ix_idempotency_records_expiry", "expires_at"),
    )

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cooperatives.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    endpoint: Mapped[str] = mapped_column(String(160), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[IdempotencyStatus] = mapped_column(
        SqlEnum(
            IdempotencyStatus,
            native_enum=False,
            create_constraint=False,
            name="ck_idempotency_records_status",
            length=16,
        ),
        nullable=False,
        default=IdempotencyStatus.PROCESSING,
        server_default=IdempotencyStatus.PROCESSING.value,
    )
    response_status: Mapped[int | None] = mapped_column(SmallInteger)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    cooperative: Mapped[Cooperative] = relationship("Cooperative")
    user: Mapped[User] = relationship("User")


__all__ = ["IdempotencyRecord"]
