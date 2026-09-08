"""质检查询的缓存白名单。"""

from __future__ import annotations

from app.models.enums import SortDirection
from app.schemas.quality_inspection import QualityInspectionListParams

_CACHEABLE_PAGE_SIZES = frozenset({10, 20, 100})


def is_cacheable_quality_list(params: QualityInspectionListParams) -> bool:
    return (
        params.page == 1
        and params.page_size in _CACHEABLE_PAGE_SIZES
        and params.sort_by == "createdAt"
        and params.sort_order is SortDirection.DESC
    )


__all__ = ["is_cacheable_quality_list"]
