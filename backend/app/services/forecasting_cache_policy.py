"""模型版本和预测结果查询的缓存白名单。"""

from __future__ import annotations

from app.models.enums import SortDirection
from app.schemas.forecasting import ModelVersionListParams

_CACHEABLE_PAGE_SIZES = frozenset({20, 100})


def is_cacheable_active_model_list(params: ModelVersionListParams) -> bool:
    """只缓存第一页、默认排序且未限定具体对象的启用模型列表。"""
    return (
        params.page == 1
        and params.page_size in _CACHEABLE_PAGE_SIZES
        and params.sort_by == "createdAt"
        and params.sort_order is SortDirection.DESC
        and params.is_active is True
        and params.warehouse_id is None
        and params.product_id is None
    )


__all__ = ["is_cacheable_active_model_list"]
