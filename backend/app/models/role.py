from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models._common import utc_now
from app.models.base import Base
from app.models.role_permission import role_permissions

if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.user import User


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("code", name="uq_roles_code"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    users: Mapped[list[User]] = relationship("User", back_populates="role")
    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )


__all__ = ["Role"]
