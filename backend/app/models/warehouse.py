from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Enum as SqlEnum,
    Uuid,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import WarehouseStatus

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.user_warehouse import UserWarehouse


class Warehouse(Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        UniqueConstraint(
            "cooperative_id", "code", name="uq_warehouses_cooperative_code"
        ),
        Index("ix_warehouses_cooperative_status", "cooperative_id", "status"),
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
    status: Mapped[WarehouseStatus] = mapped_column(
        SqlEnum(
            WarehouseStatus,
            native_enum=False,
            create_constraint=True,
            name="ck_warehouses_status",
            length=16,
        ),
        nullable=False,
        default=WarehouseStatus.ACTIVE,
        server_default=WarehouseStatus.ACTIVE.value,
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
