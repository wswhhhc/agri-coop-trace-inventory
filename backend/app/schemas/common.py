from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.models.enums import SortDirection


class BaseSchema(BaseModel):
    """所有 API Schema 的公共配置。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
    )


class ResourceMeta(BaseSchema):
    """主要业务资源的通用审计字段。"""

    id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime
    created_by: UUID | None = None


SortOrder = SortDirection


class PageParams(BaseSchema):
    """列表接口的通用分页和排序参数。"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="createdAt", min_length=1, max_length=50)
    sort_order: SortOrder = SortOrder.DESC


class PaginationMeta(BaseSchema):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class ApiResponse[T](BaseSchema):
    data: T


class ListResponse[T](BaseSchema):
    data: list[T]
    pagination: PaginationMeta


class ErrorInfo(BaseSchema):
    code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=500)
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = Field(default=None, min_length=1, max_length=64)


class ErrorResponse(BaseSchema):
    error: ErrorInfo


__all__ = [
    "ApiResponse",
    "BaseSchema",
    "ErrorInfo",
    "ErrorResponse",
    "ListResponse",
    "PageParams",
    "PaginationMeta",
    "ResourceMeta",
    "SortOrder",
]
