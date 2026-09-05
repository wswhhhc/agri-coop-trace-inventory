from __future__ import annotations

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field

from app.schemas.common import BaseSchema, PageParams

ProductUnit = Literal["KG", "TON", "BOX", "PIECE"]


class ProductCategoryCreate(BaseSchema):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)


class ProductCategoryUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class ProductCategoryListParams(PageParams):
    keyword: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class ProductCategoryData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    code: str
    name: str
    description: str | None
    is_active: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ProductCreate(BaseSchema):
    category_id: UUID
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=100)
    unit: ProductUnit
    shelf_life_days: int = Field(gt=0)
    safety_stock: Decimal = Field(ge=0, max_digits=14, decimal_places=3)


class ProductUpdate(BaseSchema):
    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    unit: ProductUnit | None = None
    shelf_life_days: int | None = Field(default=None, gt=0)
    safety_stock: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=3
    )
    is_active: bool | None = None


class ProductListParams(PageParams):
    keyword: str | None = Field(default=None, max_length=100)
    category_id: UUID | None = None
    is_active: bool | None = None
    warehouse_id: UUID | None = None


class ProductData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    category_id: UUID
    code: str
    name: str
    unit: ProductUnit
    shelf_life_days: int
    safety_stock: float
    is_active: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime


__all__ = [
    "ProductCategoryCreate",
    "ProductCategoryData",
    "ProductCategoryListParams",
    "ProductCategoryUpdate",
    "ProductCreate",
    "ProductData",
    "ProductListParams",
    "ProductUnit",
    "ProductUpdate",
]
