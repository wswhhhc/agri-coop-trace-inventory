from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import BatchStatus, enum_sql_values

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.product import Product
    from app.models.quality_inspection import QualityInspection
    from app.models.user import User


class Batch(Base):
    __tablename__ = "batches"
    __table_args__ = (
        CheckConstraint("expiry_date >= production_date", name="ck_batches_date_order"),
        CheckConstraint(
            f"status IN ({enum_sql_values(BatchStatus)})", name="ck_batches_status"
        ),
        UniqueConstraint("batch_no", name="uq_batches_batch_no"),
        UniqueConstraint("trace_code", name="uq_batches_trace_code"),
        Index(
            "ix_batches_cooperative_product_production",
            "cooperative_id",
            "product_id",
            "production_date",
        ),
        Index("ix_batches_cooperative_expiry", "cooperative_id", "expiry_date"),
    )

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_no: Mapped[str] = mapped_column(String(64), nullable=False)
    trace_code: Mapped[str] = mapped_column(String(64), nullable=False)
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    production_date: Mapped[date] = mapped_column(nullable=False)
    expiry_date: Mapped[date] = mapped_column(nullable=False)
    responsible_person: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[BatchStatus] = mapped_column(
        SqlEnum(
            BatchStatus,
            native_enum=False,
            create_constraint=False,
            name="ck_batches_status",
            length=20,
        ),
        nullable=False,
        default=BatchStatus.CREATED,
        server_default=BatchStatus.CREATED.value,
    )
    created_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    cooperative: Mapped[Cooperative] = relationship(
        "Cooperative", back_populates="batches"
    )
    product: Mapped[Product] = relationship("Product", back_populates="batches")
    creator: Mapped[User] = relationship(
        "User", back_populates="created_batches", foreign_keys=[created_by]
    )
    quality_inspections: Mapped[list[QualityInspection]] = relationship(
        "QualityInspection", back_populates="batch"
    )


__all__ = ["Batch"]
