from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, asc, desc, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models import Product, SortDirection
from app.repositories._query_helpers import contains_pattern


class ProductRepository:
    """产品数据访问仓储，查询始终带合作社和仓库上下文范围。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_scoped(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        product_id: UUID,
    ) -> Product | None:
        statement = select(Product).where(Product.id == product_id)
        for condition in self._scope_conditions(cooperative_id, warehouse_ids):
            statement = statement.where(condition)
        return await self.session.scalar(statement)

    async def list_scoped(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        keyword: str | None,
        category_id: UUID | None,
        is_active: bool | None,
        warehouse_id: UUID | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: SortDirection,
    ) -> tuple[list[Product], int]:
        conditions = self._scope_conditions(cooperative_id, warehouse_ids)
        if keyword:
            pattern = contains_pattern(keyword)
            conditions.append(
                or_(Product.code.ilike(pattern), Product.name.ilike(pattern))
            )
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if is_active is not None:
            conditions.append(Product.is_active == is_active)
        # Product is cooperative-scoped. warehouse_id is validated against the
        # auth context by the service; actual warehouse inventory filtering
        # belongs to the later inventories slice.
        del warehouse_id
        statement: Select[tuple[Product]] = select(Product).where(*conditions)
        total = await self.session.scalar(
            select(func.count(Product.id)).where(*conditions)
        )
        sort_column = {
            "code": Product.code,
            "name": Product.name,
            "createdAt": Product.created_at,
            "created_at": Product.created_at,
        }.get(sort_by, Product.created_at)
        ordering = (
            desc(sort_column)
            if sort_order is SortDirection.DESC
            else asc(sort_column)
        )
        result = await self.session.scalars(
            statement.order_by(ordering, Product.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def add(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        return product

    async def update(
        self,
        product: Product,
        values: dict[str, object],
    ) -> Product:
        for field, value in values.items():
            setattr(product, field, value)
        await self.session.flush()
        return product

    @staticmethod
    def _scope_conditions(
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(Product.cooperative_id == cooperative_id)
        if warehouse_ids is not None and not warehouse_ids:
            conditions.append(false())
        return conditions


__all__ = ["ProductRepository"]
