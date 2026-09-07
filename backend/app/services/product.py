from __future__ import annotations

import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import (
    ensure_warehouse_scope,
    permission_denied,
    resource_not_found,
)
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.core.validation import require_non_empty_update
from app.infrastructure.transaction import transaction_scope
from app.models import (
    SYSTEM_ADMIN_ROLE_CODE,
    Product,
    ProductCategory,
)
from app.repositories.product import ProductRepository
from app.repositories.product_category import ProductCategoryRepository
from app.schemas.product import (
    ProductCategoryCreate,
    ProductCategoryListParams,
    ProductCategoryUpdate,
    ProductCreate,
    ProductListParams,
    ProductUpdate,
)

PRODUCT_MANAGE_PERMISSION = "product:manage"
COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
_READ_ROLE_CODES = {
    SYSTEM_ADMIN_ROLE_CODE,
    COOPERATIVE_ADMIN_ROLE_CODE,
    "WAREHOUSE_STAFF",
}


def _require_read_role(context: AuthContext) -> None:
    if context.role_code not in _READ_ROLE_CODES:
        raise permission_denied()


def _require_manage(context: AuthContext) -> None:
    if context.role_code != COOPERATIVE_ADMIN_ROLE_CODE or not context.has_permission(
        PRODUCT_MANAGE_PERMISSION
    ):
        raise permission_denied()


def _require_cooperative(context: AuthContext, resource_label: str) -> UUID:
    if context.cooperative_id is None:
        raise AppException(
            code="BAD_REQUEST",
            message=f"{resource_label}必须关联合作社",
            status_code=400,
        )
    return context.cooperative_id


def _warehouse_ids_for_query(context: AuthContext) -> frozenset[UUID] | None:
    if context.role_code in {
        SYSTEM_ADMIN_ROLE_CODE,
        COOPERATIVE_ADMIN_ROLE_CODE,
    }:
        return None
    return context.warehouse_ids


class ProductCategoryService:
    """产品分类业务用例。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProductCategoryRepository(session)

    @staticmethod
    def ensure_read_access(context: AuthContext) -> None:
        _require_read_role(context)

    async def list(
        self,
        context: AuthContext,
        params: ProductCategoryListParams,
    ) -> tuple[list[ProductCategory], int]:
        _require_read_role(context)
        async with transaction_scope(self.session):
            return await self.repository.list_scoped(
                context.cooperative_id,
                _warehouse_ids_for_query(context),
                keyword=params.keyword,
                is_active=params.is_active,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )

    async def create(
        self,
        context: AuthContext,
        payload: ProductCategoryCreate,
    ) -> ProductCategory:
        _require_manage(context)
        cooperative_id = _require_cooperative(context, "产品分类")
        async with transaction_scope(self.session):
            return await self.repository.add(
                ProductCategory(
                    cooperative_id=cooperative_id,
                    **payload.model_dump(exclude_none=True),
                )
            )

    async def update(
        self,
        context: AuthContext,
        category_id: UUID,
        payload: ProductCategoryUpdate,
    ) -> ProductCategory:
        _require_manage(context)
        values = require_non_empty_update(payload.model_dump(exclude_unset=True))
        async with transaction_scope(self.session):
            category = await self.repository.get_scoped(
                context.cooperative_id,
                category_id,
                _warehouse_ids_for_query(context),
            )
            if category is None:
                raise resource_not_found()
            return await self.repository.update(category, values)

class ProductService:
    """产品业务用例。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProductRepository(session)
        self.category_repository = ProductCategoryRepository(session)

    @staticmethod
    def ensure_read_access(context: AuthContext) -> None:
        _require_read_role(context)

    async def list(
        self,
        context: AuthContext,
        params: ProductListParams,
    ) -> tuple[list[Product], int]:
        _require_read_role(context)
        if params.warehouse_id is not None:
            ensure_warehouse_scope(context, params.warehouse_id)
        async with transaction_scope(self.session):
            return await self.repository.list_scoped(
                context.cooperative_id,
                _warehouse_ids_for_query(context),
                keyword=params.keyword,
                category_id=params.category_id,
                is_active=params.is_active,
                warehouse_id=params.warehouse_id,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )

    async def get(self, context: AuthContext, product_id: UUID) -> Product:
        _require_read_role(context)
        async with transaction_scope(self.session):
            product = await self.repository.get_scoped(
                context.cooperative_id,
                _warehouse_ids_for_query(context),
                product_id,
            )
            if product is None:
                raise resource_not_found()
            return product

    async def create(
        self,
        context: AuthContext,
        payload: ProductCreate,
    ) -> Product:
        _require_manage(context)
        cooperative_id = _require_cooperative(context, "产品")
        async with transaction_scope(self.session):
            category = await self.category_repository.get_scoped(
                cooperative_id, payload.category_id, None
            )
            if category is None:
                raise resource_not_found()
            values = payload.model_dump(exclude_none=True)
            values["code"] = payload.code or self._new_product_code(category.code)
            return await self.repository.add(
                Product(
                    cooperative_id=cooperative_id,
                    **values,
                )
            )

    async def update(
        self,
        context: AuthContext,
        product_id: UUID,
        payload: ProductUpdate,
    ) -> Product:
        _require_manage(context)
        values = require_non_empty_update(payload.model_dump(exclude_unset=True))
        async with transaction_scope(self.session):
            product = await self.repository.get_scoped(
                context.cooperative_id,
                _warehouse_ids_for_query(context),
                product_id,
            )
            if product is None:
                raise resource_not_found()
            category_id = values.get("category_id")
            if category_id is not None:
                category = await self.category_repository.get_scoped(
                    context.cooperative_id, category_id, None
                )
                if category is None:
                    raise resource_not_found()
            return await self.repository.update(product, values)

    @staticmethod
    def _new_product_code(category_code: str) -> str:
        normalized_code = "".join(
            character if character.isalnum() else "-"
            for character in category_code.upper()
        ).strip("-") or "PRODUCT"
        return f"{normalized_code}-{secrets.token_hex(3).upper()}"

__all__ = ["ProductCategoryService", "ProductService"]
