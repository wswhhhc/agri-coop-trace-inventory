from __future__ import annotations

from uuid import UUID

from pydantic import AwareDatetime, Field

from app.models.enums import CooperativeStatus
from app.schemas.common import BaseSchema, PageParams


class CooperativeCreate(BaseSchema):
    name: str = Field(min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    contact_name: str | None = Field(default=None, max_length=50)
    contact_phone: str | None = Field(
        default=None, pattern=r"^1[3-9]\d{9}$", max_length=20
    )


class CooperativeUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    contact_name: str | None = Field(default=None, max_length=50)
    contact_phone: str | None = Field(
        default=None, pattern=r"^1[3-9]\d{9}$", max_length=20
    )
    status: CooperativeStatus | None = None


class CooperativeListParams(PageParams):
    keyword: str | None = Field(default=None, max_length=100)
    status: CooperativeStatus | None = None


class CooperativeData(BaseSchema):
    id: UUID
    code: str
    name: str
    contact_name: str | None
    contact_phone: str | None
    address: str | None
    status: CooperativeStatus
    created_at: AwareDatetime
    updated_at: AwareDatetime


__all__ = [
    "CooperativeCreate",
    "CooperativeData",
    "CooperativeListParams",
    "CooperativeUpdate",
]
