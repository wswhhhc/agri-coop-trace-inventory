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
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import UserStatus, enum_sql_values

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.cooperative import Cooperative
    from app.models.file import File
    from app.models.quality_inspection import QualityInspection
    from app.models.role import Role
    from app.models.trace_event import TraceEvent
    from app.models.user_warehouse import UserWarehouse

SYSTEM_ADMIN_ROLE_CODE = "SYSTEM_ADMIN"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("username = lower(username)", name="ck_users_username_lower"),
        CheckConstraint(
            f"status IN ({enum_sql_values(UserStatus)})", name="ck_users_status"
        ),
        UniqueConstraint("username", name="uq_users_username"),
        Index("ix_users_cooperative_status", "cooperative_id", "status"),
    )

    cooperative_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
    )
    role_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[UserStatus] = mapped_column(
        SqlEnum(
            UserStatus,
            native_enum=False,
            create_constraint=False,
            name="ck_users_status",
            length=16,
        ),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    cooperative: Mapped[Cooperative | None] = relationship(
        "Cooperative", back_populates="users"
    )
    role: Mapped[Role] = relationship("Role", back_populates="users")
    user_warehouses: Mapped[list[UserWarehouse]] = relationship(
        "UserWarehouse",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_batches: Mapped[list[Batch]] = relationship(
        "Batch", back_populates="creator", foreign_keys="Batch.created_by"
    )
    quality_inspections: Mapped[list[QualityInspection]] = relationship(
        "QualityInspection", back_populates="inspector", foreign_keys="QualityInspection.inspector_id"
    )
    trace_events: Mapped[list[TraceEvent]] = relationship(
        "TraceEvent", back_populates="creator", foreign_keys="TraceEvent.created_by"
    )
    uploaded_files: Mapped[list[File]] = relationship(
        "File", back_populates="uploader", foreign_keys="File.uploaded_by"
    )

    def validate_cooperative_scope(self) -> None:
        """校验用户是否满足合作社数据范围规则。"""
        has_cooperative = (
            self.cooperative_id is not None or self.cooperative is not None
        )
        role_code = self.role.code if self.role is not None else None
        if not has_cooperative and role_code != SYSTEM_ADMIN_ROLE_CODE:
            raise ValueError("非系统管理员用户必须关联合作社")


__all__ = ["SYSTEM_ADMIN_ROLE_CODE", "User"]
