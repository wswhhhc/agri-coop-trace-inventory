from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.quality_inspection import QualityInspection


class InspectionFile(Base):
    __tablename__ = "inspection_files"

    id = None  # type: ignore[assignment]
    updated_at = None  # type: ignore[assignment]

    inspection_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quality_inspections.id", ondelete="CASCADE"),
        primary_key=True,
    )
    file_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        primary_key=True,
    )

    inspection: Mapped[QualityInspection] = relationship(
        "QualityInspection", back_populates="file_links"
    )
    file: Mapped[File] = relationship("File", back_populates="inspection_links")


__all__ = ["InspectionFile"]
