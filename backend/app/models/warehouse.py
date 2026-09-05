from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models._common import utc_now
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.user_warehouse import UserWarehouse


class Warehouse(Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_warehouses_status"
        ),
        UniqueConstraint(
            "cooperative_id", "code", name="uq_warehouses_cooperative_code"
        ),
        Index("ix_warehouses_cooperative_status", "cooperative_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    manager_name: Mapped[str | None] = mapped_column(String(50))
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

    cooperative: Mapped[Cooperative] = relationship(
        "Cooperative", back_populates="warehouses"
    )
    user_warehouses: Mapped[list[UserWarehouse]] = relationship(
        "UserWarehouse",
        back_populates="warehouse",
        cascade="all, delete-orphan",
    )


__all__ = ["Warehouse"]
