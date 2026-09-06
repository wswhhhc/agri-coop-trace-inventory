from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.models import Product, ProductCategory
from app.schemas.common import ApiResponse, ListResponse
from app.schemas.product import (
    ProductCategoryCreate,
    ProductCategoryData,
    ProductCategoryListParams,
    ProductCategoryUpdate,
    ProductCreate,
    ProductData,
    ProductListParams,
    ProductUpdate,
)
from app.services.product import ProductCategoryService, ProductService

category_router = APIRouter(prefix="/product-categories", tags=["product-categories"])
product_router = APIRouter(prefix="/products", tags=["products"])


def get_category_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProductCategoryService:
    return ProductCategoryService(session)


def get_product_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProductService:
    return ProductService(session)


def _category_data(category: ProductCategory) -> ProductCategoryData:
    return ProductCategoryData.model_validate(category)


def _product_data(product: Product) -> ProductData:
    return ProductData.model_validate(product)


@category_router.get("", response_model=ListResponse[ProductCategoryData])
async def list_categories(
    params: Annotated[ProductCategoryListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[ProductCategoryService, Depends(get_category_service)],
) -> ListResponse[ProductCategoryData]:
    items, total = await service.list(context, params)
    return ListResponse(
        data=[_category_data(item) for item in items],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@category_router.post(
    "", response_model=ApiResponse[ProductCategoryData], status_code=201
)
async def create_category(
    payload: ProductCategoryCreate,
    context: CurrentAuthContext,
    service: Annotated[ProductCategoryService, Depends(get_category_service)],
) -> ApiResponse[ProductCategoryData]:
    return ApiResponse(data=_category_data(await service.create(context, payload)))


@category_router.patch(
    "/{categoryId}", response_model=ApiResponse[ProductCategoryData]
)
async def update_category(
    category_id: Annotated[UUID, Path(alias="categoryId")],
    payload: ProductCategoryUpdate,
    context: CurrentAuthContext,
    service: Annotated[ProductCategoryService, Depends(get_category_service)],
) -> ApiResponse[ProductCategoryData]:
    return ApiResponse(
        data=_category_data(await service.update(context, category_id, payload))
    )


@product_router.get("", response_model=ListResponse[ProductData])
async def list_products(
    params: Annotated[ProductListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ListResponse[ProductData]:
    items, total = await service.list(context, params)
    return ListResponse(
        data=[_product_data(item) for item in items],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@product_router.post("", response_model=ApiResponse[ProductData], status_code=201)
async def create_product(
    payload: ProductCreate,
    context: CurrentAuthContext,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ApiResponse[ProductData]:
    return ApiResponse(data=_product_data(await service.create(context, payload)))


@product_router.get("/{productId}", response_model=ApiResponse[ProductData])
async def get_product(
    product_id: Annotated[UUID, Path(alias="productId")],
    context: CurrentAuthContext,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ApiResponse[ProductData]:
    return ApiResponse(data=_product_data(await service.get(context, product_id)))


@product_router.patch("/{productId}", response_model=ApiResponse[ProductData])
async def update_product(
    product_id: Annotated[UUID, Path(alias="productId")],
    payload: ProductUpdate,
    context: CurrentAuthContext,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ApiResponse[ProductData]:
    return ApiResponse(
        data=_product_data(await service.update(context, product_id, payload))
    )


__all__ = ["category_router", "get_category_service", "get_product_service", "product_router"]
