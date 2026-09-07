from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.core.auth.dependencies import CurrentAuthContext
from app.core.config import Settings, get_settings
from app.infrastructure.database import get_db_session
from app.infrastructure.redis import get_redis_client
from app.schemas.common import ApiResponse, ListResponse
from app.schemas.dashboard import (
    AlertDistributionResult,
    DashboardListQueryParams,
    DashboardQueryParams,
    DashboardSummaryData,
    ForecastComparisonData,
    InventoryTrendData,
    ProductRankingData,
    ProductRankingParams,
)
from app.services.dashboard import DashboardService
from app.services.dashboard_cache import DashboardCache

router = APIRouter(tags=["dashboard"])


def get_dashboard_cache(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> DashboardCache:
    return DashboardCache(
        redis,
        key_prefix=settings.redis_key_prefix,
        ttl_seconds=settings.dashboard_cache_ttl_seconds,
    )


def get_dashboard_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cache: Annotated[DashboardCache, Depends(get_dashboard_cache)],
) -> DashboardService:
    return DashboardService(session, cache)


@router.get("/dashboard/summary", response_model=ApiResponse[DashboardSummaryData])
async def dashboard_summary(
    params: Annotated[DashboardQueryParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> ApiResponse[DashboardSummaryData]:
    return ApiResponse(data=await service.summary(context, params))


@router.get(
    "/dashboard/inventory-trends",
    response_model=ListResponse[InventoryTrendData],
)
async def dashboard_inventory_trends(
    params: Annotated[DashboardListQueryParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> ListResponse[InventoryTrendData]:
    items, total = await service.inventory_trends(context, params)
    return ListResponse(
        data=items,
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@router.get(
    "/dashboard/alert-distribution",
    response_model=ApiResponse[AlertDistributionResult],
)
async def dashboard_alert_distribution(
    params: Annotated[DashboardQueryParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> ApiResponse[AlertDistributionResult]:
    return ApiResponse(data=await service.alert_distribution(context, params))


@router.get(
    "/dashboard/product-ranking",
    response_model=ApiResponse[list[ProductRankingData]],
)
async def dashboard_product_ranking(
    params: Annotated[ProductRankingParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> ApiResponse[list[ProductRankingData]]:
    return ApiResponse(data=await service.product_ranking(context, params))


@router.get(
    "/dashboard/forecast-comparison",
    response_model=ApiResponse[list[ForecastComparisonData]],
)
async def dashboard_forecast_comparison(
    params: Annotated[DashboardQueryParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> ApiResponse[list[ForecastComparisonData]]:
    return ApiResponse(data=await service.forecast_comparison(context, params))


__all__ = ["get_dashboard_cache", "get_dashboard_service", "router"]
