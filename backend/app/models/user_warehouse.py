from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.warehouse import Warehouse


class UserWarehouse(Base):
    __tablename__ = "user_warehouses"

    # 关联表使用复合主键，不适用实体模型的单列 UUID 主键和更新时间。
    id = None
    updated_at = None

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

    user: Mapped[User] = relationship("User", back_populates="user_warehouses")
    warehouse: Mapped[Warehouse] = relationship(
        "Warehouse", back_populates="user_warehouses"
    )


__all__ = ["UserWarehouse"]
