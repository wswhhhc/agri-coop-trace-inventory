from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, Uuid, text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import InventoryTransactionType, enum_sql_values

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.cooperative import Cooperative
    from app.models.inventory_operation import InventoryOperation
    from app.models.user import User
    from app.models.warehouse import Warehouse


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        CheckConstraint(
            f"transaction_type IN ({enum_sql_values(InventoryTransactionType)})",
            name="ck_inventory_transactions_type",
        ),
        CheckConstraint(
            "quantity_before >= 0 AND quantity_after >= 0",
            name="ck_inventory_transactions_nonnegative",
        ),
        CheckConstraint(
            "quantity_delta <> 0", name="ck_inventory_transactions_delta_nonzero"
        ),
        CheckConstraint(
            "quantity_before + quantity_delta = quantity_after",
            name="ck_inventory_transactions_balance",
        ),
        CheckConstraint(
            "(transaction_type IN ('INBOUND', 'TRANSFER_IN') AND quantity_delta > 0) "
            "OR (transaction_type IN ('OUTBOUND', 'DAMAGE', 'TRANSFER_OUT') AND quantity_delta < 0) "
            "OR transaction_type = 'ADJUSTMENT'",
            name="ck_inventory_transactions_delta_direction",
        ),
        Index(
            "ix_inventory_transactions_warehouse_time",
            "cooperative_id",
            "warehouse_id",
            text("occurred_at DESC"),
        ),
        Index("ix_inventory_transactions_batch_time", "batch_id", "occurred_at"),
    )

    updated_at = None  # type: ignore[assignment]

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cooperatives.id", ondelete="RESTRICT"), nullable=False
    )
    operation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("inventory_operations.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False
    )
    batch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False
    )
    transaction_type: Mapped[InventoryTransactionType] = mapped_column(
        SqlEnum(
            InventoryTransactionType,
            native_enum=False,
            create_constraint=False,
            name="ck_inventory_transactions_type",
            length=24,
        ),
        nullable=False,
    )
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    cooperative: Mapped[Cooperative] = relationship("Cooperative")
    operation: Mapped[InventoryOperation] = relationship(
        "InventoryOperation", back_populates="transactions"
    )
    warehouse: Mapped[Warehouse] = relationship("Warehouse")
    batch: Mapped[Batch] = relationship("Batch")
    creator: Mapped[User] = relationship("User")


__all__ = ["InventoryTransaction"]
