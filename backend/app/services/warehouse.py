from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import (
    ensure_cooperative_scope,
    ensure_warehouse_scope,
    permission_denied,
    resource_not_found,
)
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.infrastructure.transaction import transaction_scope
from app.models import SYSTEM_ADMIN_ROLE_CODE, Warehouse
from app.repositories.warehouse import WarehouseRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseListParams, WarehouseUpdate

COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
WAREHOUSE_MANAGE_PERMISSION = "warehouse:manage"


class WarehouseService:
    """仓库业务用例，查询范围由认证上下文传入 Repository。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = WarehouseRepository(session)

    async def list(
        self,
        context: AuthContext,
        params: WarehouseListParams,
    ) -> tuple[list[Warehouse], int]:
        self._require_read_role(context)
        async with transaction_scope(self.session):
            return await self.repository.list_scoped(
                context.cooperative_id,
                self._warehouse_ids_for_query(context),
                keyword=params.keyword,
                status=params.status,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )

    async def get(self, context: AuthContext, warehouse_id: UUID) -> Warehouse:
        self._require_read_role(context)
        async with transaction_scope(self.session):
            warehouse = await self.repository.get_scoped(
                context.cooperative_id,
                self._warehouse_ids_for_query(context),
                warehouse_id,
            )
            if warehouse is None:
                raise resource_not_found()
            return warehouse

    async def create(
        self,
        context: AuthContext,
        payload: WarehouseCreate,
    ) -> Warehouse:
        self._require_manage_permission(context)
        target_cooperative_id = payload.cooperative_id or context.cooperative_id
        if target_cooperative_id is None:
            raise AppException(
                code="BAD_REQUEST",
                message="系统管理员创建仓库时必须提供合作社",
                status_code=400,
            )
        ensure_cooperative_scope(context, target_cooperative_id)
        values = payload.model_dump(exclude_none=True)
        values["cooperative_id"] = target_cooperative_id
        values.pop("cooperative_id", None)
        async with transaction_scope(self.session):
            return await self.repository.add(
                Warehouse(cooperative_id=target_cooperative_id, **values)
            )

    async def update(
        self,
        context: AuthContext,
        warehouse_id: UUID,
        payload: WarehouseUpdate,
    ) -> Warehouse:
        self._require_manage_permission(context)
        if context.role_code not in {
            SYSTEM_ADMIN_ROLE_CODE,
            COOPERATIVE_ADMIN_ROLE_CODE,
        }:
            ensure_warehouse_scope(context, warehouse_id)
        values = payload.model_dump(exclude_unset=True)
        if not values:
            raise AppException(
                code="BAD_REQUEST",
                message="至少提供一个需要更新的字段",
                status_code=400,
            )
        async with transaction_scope(self.session):
            warehouse = await self.repository.get_scoped(
                context.cooperative_id,
                self._warehouse_ids_for_query(context),
                warehouse_id,
            )
            if warehouse is None:
                raise resource_not_found()
            return await self.repository.update(warehouse, values)

    @staticmethod
    def _require_manage_permission(context: AuthContext) -> None:
        if not context.has_permission(WAREHOUSE_MANAGE_PERMISSION):
            raise permission_denied()

    @staticmethod
    def _require_read_role(context: AuthContext) -> None:
        if context.role_code not in {
            SYSTEM_ADMIN_ROLE_CODE,
            COOPERATIVE_ADMIN_ROLE_CODE,
            "WAREHOUSE_STAFF",
        }:
            raise permission_denied()

    @staticmethod
    def _warehouse_ids_for_query(
        context: AuthContext,
    ) -> frozenset[UUID] | None:
        if context.role_code in {
            SYSTEM_ADMIN_ROLE_CODE,
            COOPERATIVE_ADMIN_ROLE_CODE,
        }:
            return None
        return context.warehouse_ids


__all__ = ["WarehouseService"]
