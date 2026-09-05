from __future__ import annotations

from uuid import UUID

from pydantic import AwareDatetime, Field

from app.models.enums import WarehouseStatus
from app.schemas.common import BaseSchema, PageParams


class WarehouseCreate(BaseSchema):
    cooperative_id: UUID | None = None
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=50)


class WarehouseUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=50)
    status: WarehouseStatus | None = None


class WarehouseListParams(PageParams):
    keyword: str | None = Field(default=None, max_length=100)
    status: WarehouseStatus | None = None


class WarehouseData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    code: str
    name: str
    address: str | None
    manager_name: str | None
    status: WarehouseStatus
    created_at: AwareDatetime
    updated_at: AwareDatetime


__all__ = [
    "WarehouseCreate",
    "WarehouseData",
    "WarehouseListParams",
    "WarehouseUpdate",
]
