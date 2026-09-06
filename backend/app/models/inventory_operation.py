from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

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
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    InventoryOperationStatus,
    InventoryOperationType,
    enum_sql_values,
)

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.inventory_transaction import InventoryTransaction
    from app.models.user import User
    from app.models.warehouse import Warehouse


class InventoryOperation(Base):
    __tablename__ = "inventory_operations"
    __table_args__ = (
        CheckConstraint(
            f"operation_type IN ({enum_sql_values(InventoryOperationType)})",
            name="ck_inventory_operations_type",
        ),
        CheckConstraint(
            f"status IN ({enum_sql_values(InventoryOperationStatus)})",
            name="ck_inventory_operations_status",
        ),
        CheckConstraint(
            "(operation_type = 'TRANSFER' AND source_warehouse_id IS NOT NULL "
            "AND destination_warehouse_id IS NOT NULL AND source_warehouse_id <> destination_warehouse_id) "
            "OR (operation_type <> 'TRANSFER' AND source_warehouse_id IS NULL AND destination_warehouse_id IS NULL)",
            name="ck_inventory_operations_transfer_warehouses",
        ),
        UniqueConstraint("operation_no", name="uq_inventory_operations_no"),
        Index(
            "uq_inventory_operations_external_reference",
            "cooperative_id",
            "external_reference",
            unique=True,
            postgresql_where=text("external_reference IS NOT NULL"),
        ),
    )

    updated_at = None  # type: ignore[assignment]

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cooperatives.id", ondelete="RESTRICT"), nullable=False
    )
    operation_no: Mapped[str] = mapped_column(String(64), nullable=False)
    operation_type: Mapped[InventoryOperationType] = mapped_column(
        SqlEnum(
            InventoryOperationType,
            native_enum=False,
            create_constraint=False,
            name="ck_inventory_operations_type",
            length=24,
        ),
        nullable=False,
    )
    source_warehouse_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT")
    )
    destination_warehouse_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT")
    )
    external_reference: Mapped[str | None] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(String(500))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[InventoryOperationStatus] = mapped_column(
        SqlEnum(
            InventoryOperationStatus,
            native_enum=False,
            create_constraint=False,
            name="ck_inventory_operations_status",
            length=16,
        ),
        nullable=False,
        default=InventoryOperationStatus.COMPLETED,
        server_default=InventoryOperationStatus.COMPLETED.value,
    )
    created_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    cooperative: Mapped[Cooperative] = relationship("Cooperative")
    source_warehouse: Mapped[Warehouse | None] = relationship(
        "Warehouse", foreign_keys=[source_warehouse_id]
    )
    destination_warehouse: Mapped[Warehouse | None] = relationship(
        "Warehouse", foreign_keys=[destination_warehouse_id]
    )
    creator: Mapped[User] = relationship("User")
    transactions: Mapped[list[InventoryTransaction]] = relationship(
        "InventoryTransaction", back_populates="operation"
    )


__all__ = ["InventoryOperation"]
