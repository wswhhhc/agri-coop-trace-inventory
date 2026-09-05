from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import CooperativeStatus, enum_sql_values

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.product import Product
    from app.models.product_category import ProductCategory
    from app.models.user import User
    from app.models.warehouse import Warehouse


class Cooperative(Base):
    __tablename__ = "cooperatives"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({enum_sql_values(CooperativeStatus)})",
            name="ck_cooperatives_status",
        ),
        UniqueConstraint("code", name="uq_cooperatives_code"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(50))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[CooperativeStatus] = mapped_column(
        SqlEnum(
            CooperativeStatus,
            native_enum=False,
            create_constraint=False,
            name="ck_cooperatives_status",
            length=16,
        ),
        nullable=False,
        default=CooperativeStatus.ACTIVE,
        server_default=CooperativeStatus.ACTIVE.value,
    )

    users: Mapped[list[User]] = relationship("User", back_populates="cooperative")
    warehouses: Mapped[list[Warehouse]] = relationship(
        "Warehouse", back_populates="cooperative"
    )
    product_categories: Mapped[list[ProductCategory]] = relationship(
        "ProductCategory", back_populates="cooperative"
    )
    products: Mapped[list[Product]] = relationship(
        "Product", back_populates="cooperative"
    )
    batches: Mapped[list[Batch]] = relationship("Batch", back_populates="cooperative")


__all__ = ["Cooperative"]
