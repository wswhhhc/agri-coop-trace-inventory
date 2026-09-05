from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

SYSTEM_ADMIN_ROLE_CODE = "SYSTEM_ADMIN"


def _utc_now() -> datetime:
    return datetime.now(UTC)


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        Uuid(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        Uuid(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Cooperative(Base):
    __tablename__ = "cooperatives"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_cooperatives_status"
        ),
        UniqueConstraint("code", name="uq_cooperatives_code"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(50))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", server_default="ACTIVE"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    users: Mapped[list[User]] = relationship(back_populates="cooperative")
    warehouses: Mapped[list[Warehouse]] = relationship(back_populates="cooperative")


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
        default=_utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    users: Mapped[list[User]] = relationship(back_populates="role")
    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permissions,
        back_populates="roles",
    )


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
        DateTime(timezone=True), nullable=False, default=_utc_now
    )

    roles: Mapped[list[Role]] = relationship(
        secondary=role_permissions,
        back_populates="permissions",
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("username = lower(username)", name="ck_users_username_lower"),
        CheckConstraint(
            "status IN ('ACTIVE', 'LOCKED', 'INACTIVE')", name="ck_users_status"
        ),
        UniqueConstraint("username", name="uq_users_username"),
        Index("ix_users_cooperative_status", "cooperative_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cooperative_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cooperatives.id", ondelete="RESTRICT")
    )
    role_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", server_default="ACTIVE"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    cooperative: Mapped[Cooperative | None] = relationship(back_populates="users")
    role: Mapped[Role] = relationship(back_populates="users")
    user_warehouses: Mapped[list[UserWarehouse]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def validate_cooperative_scope(self) -> None:
        """校验用户是否满足合作社数据范围规则。

        数据库无法根据关联角色跨表约束该规则，因此由领域层显式校验。
        """
        has_cooperative = self.cooperative_id is not None or self.cooperative is not None
        role_code = self.role.code if self.role is not None else None
        if not has_cooperative and role_code != SYSTEM_ADMIN_ROLE_CODE:
            raise ValueError("非系统管理员用户必须关联合作社")


class Warehouse(Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_warehouses_status"
        ),
        UniqueConstraint(
            "cooperative_id", "code", name="uq_warehouses_cooperative_code"
        ),
        Index("ix_warehouses_cooperative_status", "cooperative_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    manager_name: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", server_default="ACTIVE"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    cooperative: Mapped[Cooperative] = relationship(back_populates="warehouses")
    user_warehouses: Mapped[list[UserWarehouse]] = relationship(
        back_populates="warehouse",
        cascade="all, delete-orphan",
    )


class UserWarehouse(Base):
    __tablename__ = "user_warehouses"

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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped[User] = relationship(back_populates="user_warehouses")
    warehouse: Mapped[Warehouse] = relationship(back_populates="user_warehouses")


__all__ = [
    "SYSTEM_ADMIN_ROLE_CODE",
    "Cooperative",
    "Permission",
    "Role",
    "User",
    "UserWarehouse",
    "Warehouse",
    "role_permissions",
]
