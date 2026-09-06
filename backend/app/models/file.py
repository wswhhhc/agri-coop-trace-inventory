from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.inspection_file import InspectionFile
    from app.models.user import User


class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="ck_files_size_positive"),
        UniqueConstraint("storage_key", name="uq_files_storage_key"),
    )

    # 文件元数据不可更新，文件内容不通过 ORM 覆盖。
    updated_at = None  # type: ignore[assignment]

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        nullable=False,
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    cooperative: Mapped[Cooperative] = relationship(
        "Cooperative", back_populates="files"
    )
    uploader: Mapped[User] = relationship("User", back_populates="uploaded_files")
    inspection_links: Mapped[list[InspectionFile]] = relationship(
        "InspectionFile",
        back_populates="file",
        cascade="all, delete-orphan",
    )


__all__ = ["File"]
