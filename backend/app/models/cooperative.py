from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models._common import utc_now
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.warehouse import Warehouse


class Cooperative(Base):
    __tablename__ = "cooperatives"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_cooperatives_status"
        ),
        UniqueConstraint("code", name="uq_cooperatives_code"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(50))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", server_default="ACTIVE"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    users: Mapped[list[User]] = relationship(
        "User", back_populates="cooperative"
    )
    warehouses: Mapped[list[Warehouse]] = relationship(
        "Warehouse", back_populates="cooperative"
    )


__all__ = ["Cooperative"]
