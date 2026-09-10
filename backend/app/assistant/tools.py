from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from langchain.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.context import AuthContext
from app.models.enums import (
    AlertSeverity,
    AlertStatus,
    AlertType,
    BatchStatus,
    CooperativeStatus,
    InventoryRisk,
    InventoryTransactionType,
    UserStatus,
    WarehouseStatus,
)
from app.schemas.alerting import AlertData, AlertListParams
from app.schemas.batch import BatchData, BatchListParams
from app.schemas.cooperative import CooperativeData, CooperativeListParams
from app.schemas.forecasting import (
    ForecastResultData,
    ForecastResultListParams,
    ModelVersionData,
    ModelVersionListParams,
)
from app.schemas.inventory import InventoryListParams, InventoryTransactionListParams
from app.schemas.product import ProductData, ProductListParams
from app.schemas.user import UserData, UserListParams
from app.schemas.warehouse import WarehouseData, WarehouseListParams
from app.services.alerting import AlertingService
from app.services.batch import BatchService
from app.services.cooperative import CooperativeService
from app.services.forecasting import ForecastingService
from app.services.inventory import InventoryService
from app.services.inventory_presenter import inventory_data, transaction_data
from app.services.product import ProductService
from app.services.user import UserService
from app.services.warehouse import WarehouseService


class UserQueryArgs(BaseModel):
    keyword: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=32)
    status: UserStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class CooperativeQueryArgs(BaseModel):
    keyword: str | None = Field(default=None, max_length=100)
    status: CooperativeStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class WarehouseQueryArgs(BaseModel):
    keyword: str | None = Field(default=None, max_length=100)
    status: WarehouseStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class ProductQueryArgs(BaseModel):
    keyword: str | None = Field(default=None, max_length=100)
    warehouse_name: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class BatchQueryArgs(BaseModel):
    keyword: str | None = Field(default=None, max_length=100)
    product_name: str | None = Field(default=None, max_length=100)
    warehouse_name: str | None = Field(default=None, max_length=100)
    status: BatchStatus | None = None
    production_date_from: date | None = None
    production_date_to: date | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class InventoryQueryArgs(BaseModel):
    keyword: str | None = Field(default=None, max_length=100)
    warehouse_name: str | None = Field(default=None, max_length=100)
    product_name: str | None = Field(default=None, max_length=100)
    batch_keyword: str | None = Field(default=None, max_length=100)
    stock_risk: InventoryRisk | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class TransactionQueryArgs(BaseModel):
    warehouse_name: str | None = Field(default=None, max_length=100)
    batch_keyword: str | None = Field(default=None, max_length=100)
    transaction_type: InventoryTransactionType | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class AlertQueryArgs(BaseModel):
    type: AlertType | None = None
    severity: AlertSeverity | None = None
    status: AlertStatus | None = None
    warehouse_name: str | None = Field(default=None, max_length=100)
    product_name: str | None = Field(default=None, max_length=100)
    batch_keyword: str | None = Field(default=None, max_length=100)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class ModelVersionQueryArgs(BaseModel):
    warehouse_name: str | None = Field(default=None, max_length=100)
    product_name: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class ForecastQueryArgs(BaseModel):
    warehouse_name: str | None = Field(default=None, max_length=100)
    product_name: str | None = Field(default=None, max_length=100)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


def _page(total: int, page: int, page_size: int) -> dict[str, int]:
    return {
        "totalItems": total,
        "page": page,
        "pageSize": page_size,
    }


def _result(
    resource: str,
    items: list[dict[str, object]],
    total: int,
    page: int,
    page_size: int,
) -> dict[str, object]:
    return {
        "resource": resource,
        "items": items,
        "pagination": _page(total, page, page_size),
    }


def _dump(model: Any) -> dict[str, object]:
    return model.model_dump(mode="json", by_alias=True)


def _user_dump(user: Any) -> dict[str, object]:
    return _dump(
        UserData(
            id=user.id,
            username=user.username,
            display_name=user.real_name,
            role=user.role.code if user.role is not None else "",
            cooperative_id=user.cooperative_id,
            warehouse_ids=sorted(item.warehouse_id for item in user.user_warehouses),
            phone=user.phone,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


class QueryToolFactory:
    """为一次请求构造带认证上下文的只读工具。"""

    def __init__(self, session: AsyncSession, context: AuthContext) -> None:
        self.context = context
        self.user_service = UserService(session)
        self.cooperative_service = CooperativeService(session)
        self.warehouse_service = WarehouseService(session)
        self.product_service = ProductService(session)
        self.batch_service = BatchService(session)
        self.inventory_service = InventoryService(session)
        self.alerting_service = AlertingService(session)
        self.forecasting_service = ForecastingService(session)

    def build(self) -> list[Any]:
        tools: list[Any] = []
        roles = self.context.role_code

        @tool(args_schema=UserQueryArgs)
        async def query_users(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的后台用户。"""
            return await self._query_users(**kwargs)

        @tool(args_schema=CooperativeQueryArgs)
        async def query_cooperatives(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的合作社。"""
            return await self._query_cooperatives(**kwargs)

        @tool(args_schema=WarehouseQueryArgs)
        async def query_warehouses(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的仓库。"""
            return await self._query_warehouses(**kwargs)

        @tool(args_schema=ProductQueryArgs)
        async def query_products(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的产品。"""
            return await self._query_products(**kwargs)

        @tool(args_schema=BatchQueryArgs)
        async def query_batches(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的农产品批次。"""
            return await self._query_batches(**kwargs)

        @tool(args_schema=InventoryQueryArgs)
        async def query_inventories(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的仓库批次库存。"""
            return await self._query_inventories(**kwargs)

        @tool(args_schema=TransactionQueryArgs)
        async def query_inventory_transactions(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的库存流水。"""
            return await self._query_inventory_transactions(**kwargs)

        @tool(args_schema=AlertQueryArgs)
        async def query_alerts(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的库存和质检预警。"""
            return await self._query_alerts(**kwargs)

        @tool(args_schema=ModelVersionQueryArgs)
        async def query_model_versions(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的预测模型版本。"""
            return await self._query_model_versions(**kwargs)

        @tool(args_schema=ForecastQueryArgs)
        async def query_forecast_results(**kwargs: Any) -> dict[str, object]:
            """查询当前用户有权限查看的需求预测结果。"""
            return await self._query_forecast_results(**kwargs)

        if self.context.has_permission("user:manage") and roles in {
            "SYSTEM_ADMIN",
            "COOPERATIVE_ADMIN",
        }:
            tools.append(query_users)
        if self.context.has_permission("cooperative:manage"):
            tools.append(query_cooperatives)
        if roles in {"SYSTEM_ADMIN", "COOPERATIVE_ADMIN", "WAREHOUSE_STAFF"}:
            tools.extend([query_warehouses, query_products, query_batches])
        if self.context.has_permission("inventory:read"):
            tools.extend([query_inventories, query_inventory_transactions])
        if self.context.has_permission("alert:read"):
            tools.append(query_alerts)
        if self.context.has_permission("model:read"):
            tools.extend([query_model_versions, query_forecast_results])
        return tools

    async def _resolve_warehouse(
        self, name: str | None
    ) -> UUID | dict[str, object] | None:
        if not name:
            return None
        items, total = await self.warehouse_service.list(
            self.context, WarehouseListParams(keyword=name, page_size=20)
        )
        exact = [item for item in items if item.name == name]
        if len(exact) == 1:
            return exact[0].id
        if total == 1:
            return items[0].id
        if not items:
            return {"clarification": f"没有找到名为“{name}”的仓库，请确认名称。"}
        return {
            "clarification": f"“{name}”匹配到多个仓库，请提供更完整的名称。",
            "choices": [item.name for item in items[:10]],
        }

    async def _resolve_product(
        self, name: str | None
    ) -> UUID | dict[str, object] | None:
        if not name:
            return None
        items, total = await self.product_service.list(
            self.context, ProductListParams(keyword=name, page_size=20)
        )
        exact = [item for item in items if item.name == name]
        if len(exact) == 1:
            return exact[0].id
        if total == 1:
            return items[0].id
        if not items:
            return {"clarification": f"没有找到名为“{name}”的产品，请确认名称。"}
        return {
            "clarification": f"“{name}”匹配到多个产品，请提供更完整的名称。",
            "choices": [item.name for item in items[:10]],
        }

    async def _resolve_batch(
        self,
        keyword: str | None,
        *,
        product_id: UUID | None = None,
        warehouse_id: UUID | None = None,
    ) -> UUID | dict[str, object] | None:
        if not keyword:
            return None
        items, total = await self.batch_service.list(
            self.context,
            BatchListParams(
                keyword=keyword,
                product_id=product_id,
                warehouse_id=warehouse_id,
                page_size=20,
            ),
        )
        exact = [item for item in items if item.batch_no == keyword]
        if len(exact) == 1:
            return exact[0].id
        if total == 1:
            return items[0].id
        if not items:
            return {"clarification": f"没有找到批次“{keyword}”，请确认批次号。"}
        return {
            "clarification": f"“{keyword}”匹配到多个批次，请提供完整批次号。",
            "choices": [item.batch_no for item in items[:10]],
        }

    async def _query_users(self, **kwargs: Any) -> dict[str, object]:
        args = UserQueryArgs(**kwargs)
        items, total = await self.user_service.list_users(
            self.context, UserListParams(**args.model_dump())
        )
        return _result(
            "users",
            [_user_dump(item) for item in items],
            total,
            args.page,
            args.page_size,
        )

    async def _query_cooperatives(self, **kwargs: Any) -> dict[str, object]:
        args = CooperativeQueryArgs(**kwargs)
        items, total = await self.cooperative_service.list(
            self.context, CooperativeListParams(**args.model_dump())
        )
        return _result(
            "cooperatives",
            [_dump(CooperativeData.model_validate(item)) for item in items],
            total,
            args.page,
            args.page_size,
        )

    async def _query_warehouses(self, **kwargs: Any) -> dict[str, object]:
        args = WarehouseQueryArgs(**kwargs)
        items, total = await self.warehouse_service.list(
            self.context, WarehouseListParams(**args.model_dump())
        )
        return _result(
            "warehouses",
            [_dump(WarehouseData.model_validate(item)) for item in items],
            total,
            args.page,
            args.page_size,
        )

    async def _query_products(self, **kwargs: Any) -> dict[str, object]:
        args = ProductQueryArgs(**kwargs)
        warehouse_id = await self._resolve_warehouse(args.warehouse_name)
        if isinstance(warehouse_id, dict):
            return warehouse_id
        items, total = await self.product_service.list(
            self.context,
            ProductListParams(
                keyword=args.keyword,
                is_active=args.is_active,
                warehouse_id=warehouse_id,
                page=args.page,
                page_size=args.page_size,
            ),
        )
        return _result(
            "products",
            [_dump(ProductData.model_validate(item)) for item in items],
            total,
            args.page,
            args.page_size,
        )

    async def _query_batches(self, **kwargs: Any) -> dict[str, object]:
        args = BatchQueryArgs(**kwargs)
        product_id = await self._resolve_product(args.product_name)
        if isinstance(product_id, dict):
            return product_id
        warehouse_id = await self._resolve_warehouse(args.warehouse_name)
        if isinstance(warehouse_id, dict):
            return warehouse_id
        items, total = await self.batch_service.list(
            self.context,
            BatchListParams(
                keyword=args.keyword,
                product_id=product_id,
                warehouse_id=warehouse_id,
                status=args.status,
                production_date_from=args.production_date_from,
                production_date_to=args.production_date_to,
                page=args.page,
                page_size=args.page_size,
            ),
        )
        return _result(
            "batches",
            [_dump(BatchData.model_validate(item)) for item in items],
            total,
            args.page,
            args.page_size,
        )

    async def _query_inventories(self, **kwargs: Any) -> dict[str, object]:
        args = InventoryQueryArgs(**kwargs)
        warehouse_id = await self._resolve_warehouse(args.warehouse_name)
        if isinstance(warehouse_id, dict):
            return warehouse_id
        product_id = await self._resolve_product(args.product_name)
        if isinstance(product_id, dict):
            return product_id
        batch_id = await self._resolve_batch(
            args.batch_keyword, product_id=product_id, warehouse_id=warehouse_id
        )
        if isinstance(batch_id, dict):
            return batch_id
        items, total = await self.inventory_service.list_current(
            self.context,
            InventoryListParams(
                warehouse_id=warehouse_id,
                product_id=product_id,
                batch_id=batch_id,
                keyword=args.keyword,
                stock_risk=args.stock_risk,
                page=args.page,
                page_size=args.page_size,
            ),
        )
        return _result(
            "inventories",
            [_dump(inventory_data(item)) for item in items],
            total,
            args.page,
            args.page_size,
        )

    async def _query_inventory_transactions(self, **kwargs: Any) -> dict[str, object]:
        args = TransactionQueryArgs(**kwargs)
        warehouse_id = await self._resolve_warehouse(args.warehouse_name)
        if isinstance(warehouse_id, dict):
            return warehouse_id
        batch_id = await self._resolve_batch(
            args.batch_keyword, warehouse_id=warehouse_id
        )
        if isinstance(batch_id, dict):
            return batch_id
        items, total = await self.inventory_service.list_transactions(
            self.context,
            InventoryTransactionListParams(
                warehouse_id=warehouse_id,
                batch_id=batch_id,
                transaction_type=args.transaction_type,
                page=args.page,
                page_size=args.page_size,
            ),
        )
        return _result(
            "inventoryTransactions",
            [_dump(transaction_data(item)) for item in items],
            total,
            args.page,
            args.page_size,
        )

    async def _query_alerts(self, **kwargs: Any) -> dict[str, object]:
        args = AlertQueryArgs(**kwargs)
        warehouse_id = await self._resolve_warehouse(args.warehouse_name)
        if isinstance(warehouse_id, dict):
            return warehouse_id
        product_id = await self._resolve_product(args.product_name)
        if isinstance(product_id, dict):
            return product_id
        batch_id = await self._resolve_batch(
            args.batch_keyword, product_id=product_id, warehouse_id=warehouse_id
        )
        if isinstance(batch_id, dict):
            return batch_id
        items, total = await self.alerting_service.list_alerts(
            self.context,
            AlertListParams(
                type=args.type,
                severity=args.severity,
                status=args.status,
                warehouse_id=warehouse_id,
                product_id=product_id,
                batch_id=batch_id,
                page=args.page,
                page_size=args.page_size,
            ),
        )
        return _result(
            "alerts",
            [_dump(AlertData.model_validate(item)) for item in items],
            total,
            args.page,
            args.page_size,
        )

    async def _query_model_versions(self, **kwargs: Any) -> dict[str, object]:
        args = ModelVersionQueryArgs(**kwargs)
        warehouse_id = await self._resolve_warehouse(args.warehouse_name)
        if isinstance(warehouse_id, dict):
            return warehouse_id
        product_id = await self._resolve_product(args.product_name)
        if isinstance(product_id, dict):
            return product_id
        items, total = await self.forecasting_service.list_model_versions(
            self.context,
            ModelVersionListParams(
                warehouse_id=warehouse_id,
                product_id=product_id,
                is_active=args.is_active,
                page=args.page,
                page_size=args.page_size,
            ),
        )
        return _result(
            "modelVersions",
            [_dump(ModelVersionData.model_validate(item)) for item in items],
            total,
            args.page,
            args.page_size,
        )

    async def _query_forecast_results(self, **kwargs: Any) -> dict[str, object]:
        args = ForecastQueryArgs(**kwargs)
        warehouse_id = await self._resolve_warehouse(args.warehouse_name)
        if isinstance(warehouse_id, dict):
            return warehouse_id
        product_id = await self._resolve_product(args.product_name)
        if isinstance(product_id, dict):
            return product_id
        items, total = await self.forecasting_service.list_forecast_results(
            self.context,
            ForecastResultListParams(
                warehouse_id=warehouse_id,
                product_id=product_id,
                page=args.page,
                page_size=args.page_size,
            ),
        )
        return _result(
            "forecastResults",
            [_dump(ForecastResultData.model_validate(item)) for item in items],
            total,
            args.page,
            args.page_size,
        )


__all__ = ["QueryToolFactory"]
