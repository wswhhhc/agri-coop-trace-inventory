from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.quality_inspection import QualityInspection


class QualityInspectionItem(Base):
    __tablename__ = "quality_inspection_items"
    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="ck_inspection_items_sort_order"),
        UniqueConstraint("inspection_id", "item_name", name="uq_inspection_items_name"),
    )

    # 明细表只有 created_at，没有 updated_at。
    updated_at = None  # type: ignore[assignment]

    inspection_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quality_inspections.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20))
    standard_value: Mapped[str] = mapped_column(String(100), nullable=False)
    result_value: Mapped[str] = mapped_column(String(100), nullable=False)
    is_qualified: Mapped[bool] = mapped_column(nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")

    inspection: Mapped[QualityInspection] = relationship(
        "QualityInspection", back_populates="items"
    )


__all__ = ["QualityInspectionItem"]
