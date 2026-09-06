from __future__ import annotations

from math import ceil

from app.schemas.common import PaginationMeta


def build_pagination_meta(total: int, page: int, page_size: int) -> PaginationMeta:
    """根据列表查询结果构造统一的分页元数据。"""
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=ceil(total / page_size) if total else 0,
    )


__all__ = ["build_pagination_meta"]
