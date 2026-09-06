from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.cooperative import Cooperative
    from app.models.warehouse import Warehouse


class Inventory(Base):
    __tablename__ = "inventories"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventories_quantity"),
        CheckConstraint(
            "locked_quantity >= 0 AND locked_quantity <= quantity",
            name="ck_inventories_locked_quantity",
        ),
        CheckConstraint("version >= 0", name="ck_inventories_version"),
        UniqueConstraint("warehouse_id", "batch_id", name="uq_inventories_warehouse_batch"),
        Index("ix_inventories_cooperative_warehouse", "cooperative_id", "warehouse_id"),
    )

    created_at = None  # type: ignore[assignment]

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cooperatives.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False
    )
    batch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, default=Decimal(0), server_default="0"
    )
    locked_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, default=Decimal(0), server_default="0"
    )
    version: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")

    cooperative: Mapped[Cooperative] = relationship("Cooperative")
    warehouse: Mapped[Warehouse] = relationship("Warehouse")
    batch: Mapped[Batch] = relationship("Batch")


__all__ = ["Inventory"]
