from __future__ import annotations

import logging
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import resource_not_found
from app.core.auth.context import AuthContext
from app.infrastructure.transaction import transaction_scope
from app.models import Inventory, InventoryTransaction
from app.repositories.idempotency_record import IdempotencyRecordRepository
from app.repositories.inventory import InventoryRepository
from app.schemas.inventory import (
    InventoryIssueCreate,
    InventoryListParams,
    InventoryLossCreate,
    InventoryReceiptCreate,
    InventoryTransactionListParams,
    StocktakeCreate,
    StockTransferCreate,
)
from app.services.inventory_mutations import InventoryMutationService
from app.services.inventory_policy import (
    ensure_optional_warehouse_scope,
    require_read,
    warehouse_ids,
)
from app.services.traceability import TraceabilityCache

logger = logging.getLogger(__name__)


class InventoryService:
    """库存业务门面；查询和变更分别委托给专门的用例服务。"""

    def __init__(
        self,
        session: AsyncSession,
        cache: TraceabilityCache | None = None,
        alert_scheduler: Callable[..., object] | None = None,
    ) -> None:
        self.session = session
        self.alert_scheduler = alert_scheduler
        repository = InventoryRepository(session)
        self.repository = repository
        self._mutation_service = InventoryMutationService(
            session,
            repository,
            IdempotencyRecordRepository(session),
            cache,
        )

    def _schedule_alert_scan(self, context: AuthContext) -> None:
        if self.alert_scheduler is None or context.cooperative_id is None:
            return
        try:
            self.alert_scheduler(args=[str(context.cooperative_id)], kwargs={})
        except Exception:
            logger.exception("库存变更后提交预警扫描任务失败 cooperative_id=%s", context.cooperative_id)

    async def list_current(
        self, context: AuthContext, params: InventoryListParams
    ) -> tuple[list[Inventory], int]:
        require_read(context)
        ensure_optional_warehouse_scope(context, params.warehouse_id)
        async with transaction_scope(self.session):
            return await self.repository.list_inventory(
                context.cooperative_id,
                warehouse_ids(context),
                warehouse_id=params.warehouse_id,
                product_id=params.product_id,
                batch_id=params.batch_id,
                keyword=params.keyword,
                stock_risk=params.stock_risk.value if params.stock_risk else None,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order.value,
            )

    async def get(self, context: AuthContext, inventory_id: UUID) -> Inventory:
        require_read(context)
        async with transaction_scope(self.session):
            inventory = await self.repository.get_inventory(
                context.cooperative_id, warehouse_ids(context), inventory_id
            )
            if inventory is None:
                raise resource_not_found()
            return inventory

    async def list_transactions(
        self, context: AuthContext, params: InventoryTransactionListParams
    ) -> tuple[list[InventoryTransaction], int]:
        require_read(context)
        ensure_optional_warehouse_scope(context, params.warehouse_id)
        async with transaction_scope(self.session):
            return await self.repository.list_transactions(
                context.cooperative_id,
                warehouse_ids(context),
                warehouse_id=params.warehouse_id,
                batch_id=params.batch_id,
                transaction_type=params.transaction_type,
                occurred_at_from=params.occurred_at_from,
                occurred_at_to=params.occurred_at_to,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order.value,
            )

    async def get_transaction(
        self, context: AuthContext, transaction_id: UUID
    ) -> InventoryTransaction:
        require_read(context)
        async with transaction_scope(self.session):
            transaction = await self.repository.get_transaction(
                context.cooperative_id,
                warehouse_ids(context),
                transaction_id,
            )
            if transaction is None:
                raise resource_not_found()
            return transaction

    async def receive(
        self, context: AuthContext, payload: InventoryReceiptCreate, idempotency_key: str
    ) -> dict[str, object]:
        result = await self._mutation_service.receive(context, payload, idempotency_key)
        self._schedule_alert_scan(context)
        return result

    async def issue(
        self, context: AuthContext, payload: InventoryIssueCreate, idempotency_key: str
    ) -> dict[str, object]:
        result = await self._mutation_service.issue(context, payload, idempotency_key)
        self._schedule_alert_scan(context)
        return result

    async def loss(
        self, context: AuthContext, payload: InventoryLossCreate, idempotency_key: str
    ) -> dict[str, object]:
        result = await self._mutation_service.loss(context, payload, idempotency_key)
        self._schedule_alert_scan(context)
        return result

    async def transfer(
        self, context: AuthContext, payload: StockTransferCreate, idempotency_key: str
    ) -> dict[str, object]:
        result = await self._mutation_service.transfer(context, payload, idempotency_key)
        self._schedule_alert_scan(context)
        return result

    async def stocktake(
        self, context: AuthContext, payload: StocktakeCreate, idempotency_key: str
    ) -> dict[str, object]:
        result = await self._mutation_service.stocktake(context, payload, idempotency_key)
        self._schedule_alert_scan(context)
        return result

__all__ = ["InventoryService"]
