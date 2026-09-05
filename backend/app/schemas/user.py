from __future__ import annotations

from uuid import UUID

from pydantic import AwareDatetime, Field

from app.models.enums import UserStatus
from app.schemas.common import BaseSchema, PageParams


class UserCreate(BaseSchema):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-z0-9][a-z0-9_.-]{2,49}$",
    )
    display_name: str = Field(min_length=1, max_length=50)
    role: str = Field(min_length=1, max_length=32)
    cooperative_id: UUID | None = None
    warehouse_ids: list[UUID] = Field(default_factory=list, max_length=100)
    phone: str | None = Field(
        default=None, pattern=r"^1[3-9]\d{9}$", max_length=20
    )


class UserUpdate(BaseSchema):
    display_name: str | None = Field(default=None, min_length=1, max_length=50)
    role: str | None = Field(default=None, min_length=1, max_length=32)
    status: UserStatus | None = None
    phone: str | None = Field(
        default=None, pattern=r"^1[3-9]\d{9}$", max_length=20
    )


class UserListParams(PageParams):
    keyword: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=32)
    status: UserStatus | None = None


class WarehouseAssignment(BaseSchema):
    warehouse_ids: list[UUID] = Field(default_factory=list, max_length=100)


class UserData(BaseSchema):
    id: UUID
    username: str
    display_name: str
    role: str
    cooperative_id: UUID | None
    warehouse_ids: list[UUID]
    phone: str | None
    status: UserStatus
    created_at: AwareDatetime
    updated_at: AwareDatetime


class UserCreateData(UserData):
    initial_password: str


class PasswordResetData(BaseSchema):
    temporary_password: str


__all__ = [
    "PasswordResetData",
    "UserCreate",
    "UserCreateData",
    "UserData",
    "UserListParams",
    "UserUpdate",
    "WarehouseAssignment",
]
