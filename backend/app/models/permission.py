from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models._common import utc_now
from app.models.base import Base
from app.models.role_permission import role_permissions

if TYPE_CHECKING:
    from app.models.role import Role


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("code", name="uq_permissions_code"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    module: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
    )


__all__ = ["Permission"]
