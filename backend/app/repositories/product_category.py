from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, asc, desc, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models import ProductCategory, SortDirection
from app.repositories._query_helpers import contains_pattern


class ProductCategoryRepository:
    """产品分类数据访问仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_scoped(
        self,
        cooperative_id: UUID | None,
        category_id: UUID,
        warehouse_ids: frozenset[UUID] | None,
    ) -> ProductCategory | None:
        statement = select(ProductCategory).where(ProductCategory.id == category_id)
        for condition in self._scope_conditions(cooperative_id, warehouse_ids):
            statement = statement.where(condition)
        return await self.session.scalar(statement)

    async def list_scoped(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        keyword: str | None,
        is_active: bool | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: SortDirection,
    ) -> tuple[list[ProductCategory], int]:
        conditions = self._scope_conditions(cooperative_id, warehouse_ids)
        if keyword:
            pattern = contains_pattern(keyword)
            conditions.append(
                or_(
                    ProductCategory.code.ilike(pattern),
                    ProductCategory.name.ilike(pattern),
                )
            )
        if is_active is not None:
            conditions.append(ProductCategory.is_active == is_active)
        statement: Select[tuple[ProductCategory]] = select(ProductCategory).where(
            *conditions
        )
        total = await self.session.scalar(
            select(func.count(ProductCategory.id)).where(*conditions)
        )
        sort_column = {
            "code": ProductCategory.code,
            "name": ProductCategory.name,
            "createdAt": ProductCategory.created_at,
            "created_at": ProductCategory.created_at,
        }.get(sort_by, ProductCategory.created_at)
        ordering = (
            desc(sort_column)
            if sort_order is SortDirection.DESC
            else asc(sort_column)
        )
        result = await self.session.scalars(
            statement.order_by(ordering, ProductCategory.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def add(self, category: ProductCategory) -> ProductCategory:
        self.session.add(category)
        await self.session.flush()
        return category

    async def update(
        self,
        category: ProductCategory,
        values: dict[str, object],
    ) -> ProductCategory:
        for field, value in values.items():
            setattr(category, field, value)
        await self.session.flush()
        return category

    @staticmethod
    def _scope_conditions(
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(ProductCategory.cooperative_id == cooperative_id)
        if warehouse_ids is not None and not warehouse_ids:
            conditions.append(false())
        return conditions


__all__ = ["ProductCategoryRepository"]
