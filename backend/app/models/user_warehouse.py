from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models._common import utc_now
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.warehouse import Warehouse


class UserWarehouse(Base):
    __tablename__ = "user_warehouses"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped[User] = relationship("User", back_populates="user_warehouses")
    warehouse: Mapped[Warehouse] = relationship(
        "Warehouse", back_populates="user_warehouses"
    )


__all__ = ["UserWarehouse"]
