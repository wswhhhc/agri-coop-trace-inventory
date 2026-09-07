"""基础参考数据查询的缓存白名单。"""

from __future__ import annotations

from app.models.enums import SortDirection
from app.schemas.common import PageParams

_CACHEABLE_PAGE_SIZES = frozenset({20, 100})


def is_cacheable_reference_list(params: PageParams) -> bool:
    """只缓存常用的无关键词第一页，限制 key 组合数量。"""
    return (
        params.page == 1
        and params.page_size in _CACHEABLE_PAGE_SIZES
        and params.sort_by == "createdAt"
        and params.sort_order is SortDirection.DESC
        and getattr(params, "keyword", None) is None
        and all(
            getattr(params, field_name, None) is None
            for field_name in ("category_id", "warehouse_id", "is_active", "status")
        )
    )


__all__ = ["is_cacheable_reference_list"]
