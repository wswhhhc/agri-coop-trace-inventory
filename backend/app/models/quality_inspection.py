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
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import InspectionConclusion, enum_sql_values

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.cooperative import Cooperative
    from app.models.inspection_file import InspectionFile
    from app.models.quality_inspection_item import QualityInspectionItem
    from app.models.user import User


class QualityInspection(Base):
    __tablename__ = "quality_inspections"
    __table_args__ = (
        CheckConstraint(
            f"conclusion IN ({enum_sql_values(InspectionConclusion)})",
            name="ck_quality_inspections_conclusion",
        ),
        UniqueConstraint(
            "cooperative_id",
            "inspection_no",
            name="uq_quality_inspections_cooperative_no",
        ),
        Index("ix_quality_inspections_batch_time", "batch_id", "inspected_at"),
        Index("ix_quality_inspections_original", "original_inspection_id"),
    )

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    inspection_no: Mapped[str] = mapped_column(String(64), nullable=False)
    inspected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    inspector_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    conclusion: Mapped[InspectionConclusion] = mapped_column(
        SqlEnum(
            InspectionConclusion,
            native_enum=False,
            create_constraint=False,
            name="ck_quality_inspections_conclusion",
            length=16,
        ),
        nullable=False,
        default=InspectionConclusion.PENDING,
        server_default=InspectionConclusion.PENDING.value,
    )
    remarks: Mapped[str | None] = mapped_column(String(500))
    original_inspection_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quality_inspections.id", ondelete="RESTRICT"),
    )

    cooperative: Mapped[Cooperative] = relationship(
        "Cooperative", back_populates="quality_inspections"
    )
    batch: Mapped[Batch] = relationship("Batch", back_populates="quality_inspections")
    inspector: Mapped[User] = relationship(
        "User", back_populates="quality_inspections", foreign_keys=[inspector_id]
    )
    original_inspection: Mapped[QualityInspection | None] = relationship(
        "QualityInspection",
        remote_side="QualityInspection.id",
        back_populates="corrections",
        foreign_keys=[original_inspection_id],
    )
    corrections: Mapped[list[QualityInspection]] = relationship(
        "QualityInspection",
        back_populates="original_inspection",
        foreign_keys=[original_inspection_id],
    )
    items: Mapped[list[QualityInspectionItem]] = relationship(
        "QualityInspectionItem",
        back_populates="inspection",
        cascade="all, delete-orphan",
        order_by="QualityInspectionItem.sort_order",
    )
    file_links: Mapped[list[InspectionFile]] = relationship(
        "InspectionFile",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )


__all__ = ["QualityInspection"]
