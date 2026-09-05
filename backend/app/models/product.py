from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.cooperative import Cooperative
    from app.models.product_category import ProductCategory


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("shelf_life_days > 0", name="ck_products_shelf_life"),
        CheckConstraint("safety_stock >= 0", name="ck_products_safety_stock"),
        UniqueConstraint("cooperative_id", "code", name="uq_products_cooperative_code"),
        Index(
            "ix_products_cooperative_active_name", "cooperative_id", "is_active", "name"
        ),
    )

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    shelf_life_days: Mapped[int] = mapped_column(nullable=False)
    safety_stock: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, default=Decimal(0), server_default="0"
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="true"
    )

    cooperative: Mapped[Cooperative] = relationship(
        "Cooperative", back_populates="products"
    )
    category: Mapped[ProductCategory] = relationship(
        "ProductCategory", back_populates="products"
    )
    batches: Mapped[list[Batch]] = relationship("Batch", back_populates="product")


__all__ = ["Product"]
