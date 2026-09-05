from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.product import Product


class ProductCategory(Base):
    __tablename__ = "product_categories"
    __table_args__ = (
        UniqueConstraint(
            "cooperative_id", "code", name="uq_product_categories_cooperative_code"
        ),
        UniqueConstraint(
            "cooperative_id", "name", name="uq_product_categories_cooperative_name"
        ),
    )

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="true"
    )

    cooperative: Mapped[Cooperative] = relationship(
        "Cooperative", back_populates="product_categories"
    )
    products: Mapped[list[Product]] = relationship("Product", back_populates="category")


__all__ = ["ProductCategory"]
