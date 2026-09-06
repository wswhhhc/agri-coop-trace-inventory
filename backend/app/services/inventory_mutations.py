from __future__ import annotations

from decimal import Decimal
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import ensure_warehouse_scope, resource_not_found
from app.core.auth.context import AuthContext
from app.core.exceptions import (
    AppException,
    InsufficientInventoryError,
    StatusNotAllowedError,
)
from app.infrastructure.transaction import transaction_scope
from app.models import (
    Batch,
    BatchStatus,
    InventoryOperation,
    InventoryOperationStatus,
    InventoryOperationType,
    InventoryTransaction,
    InventoryTransactionType,
    Warehouse,
    WarehouseStatus,
)
from app.repositories.idempotency_record import IdempotencyRecordRepository
from app.repositories.inventory import InventoryRepository
from app.schemas.inventory import (
    InventoryIssueCreate,
    InventoryLossCreate,
    InventoryReceiptCreate,
    StocktakeCreate,
    StocktakeData,
    StockTransferCreate,
    TransferData,
)
from app.services.inventory_idempotency import InventoryIdempotency
from app.services.inventory_policy import (
    WAREHOUSE_STAFF_ROLE_CODE,
    require_cooperative,
    require_write,
    warehouse_ids,
)
from app.services.inventory_presenter import transaction_dict


def sync_batch_status(batch: Batch, quantity: Decimal) -> None:
    if batch.status in {BatchStatus.BLOCKED, BatchStatus.EXPIRED}:
        return
    batch.status = BatchStatus.IN_STOCK if quantity > 0 else BatchStatus.DEPLETED


class InventoryMutationService:
    """库存写操作；保证当前库存、操作头和流水在同一事务内更新。"""

    def __init__(
        self,
        session: AsyncSession,
        repository: InventoryRepository,
        idempotency_repository: IdempotencyRecordRepository,
    ) -> None:
        self.session = session
        self.repository = repository
        self.idempotency = InventoryIdempotency(idempotency_repository)

    async def receive(
        self, context: AuthContext, payload: InventoryReceiptCreate, idempotency_key: str
    ) -> dict[str, object]:
        return await self._change_single(
            context,
            payload,
            idempotency_key,
            endpoint="/api/v1/inventory-receipts",
            operation_type=InventoryOperationType.INBOUND,
            transaction_type=InventoryTransactionType.INBOUND,
            quantity_delta=payload.quantity,
            reference_no=payload.reference_no,
            reason=payload.remark,
        )

    async def issue(
        self, context: AuthContext, payload: InventoryIssueCreate, idempotency_key: str
    ) -> dict[str, object]:
        reason = payload.remark
        if payload.destination:
            reason = f"去向：{payload.destination}" + (f"；{reason}" if reason else "")
        return await self._change_single(
            context,
            payload,
            idempotency_key,
            endpoint="/api/v1/inventory-issues",
            operation_type=InventoryOperationType.OUTBOUND,
            transaction_type=InventoryTransactionType.OUTBOUND,
            quantity_delta=-payload.quantity,
            reference_no=payload.reference_no,
            reason=reason,
        )

    async def loss(
        self, context: AuthContext, payload: InventoryLossCreate, idempotency_key: str
    ) -> dict[str, object]:
        return await self._change_single(
            context,
            payload,
            idempotency_key,
            endpoint="/api/v1/inventory-losses",
            operation_type=InventoryOperationType.DAMAGE,
            transaction_type=InventoryTransactionType.DAMAGE,
            quantity_delta=-payload.quantity,
            reference_no=None,
            reason=payload.reason + (f"；{payload.remark}" if payload.remark else ""),
        )

    async def transfer(
        self, context: AuthContext, payload: StockTransferCreate, idempotency_key: str
    ) -> dict[str, object]:
        require_write(context)
        cooperative_id = require_cooperative(context)
        endpoint = "/api/v1/stock-transfers"
        async with transaction_scope(self.session):
            replay = await self.idempotency.prepare(
                context, cooperative_id, endpoint, idempotency_key, payload
            )
            if replay is not None:
                return replay
            await self._get_active_warehouse(context, cooperative_id, payload.source_warehouse_id)
            await self._get_active_warehouse(context, cooperative_id, payload.target_warehouse_id)
            batch = await self._get_movable_batch(cooperative_id, payload.batch_id)

            first, second = sorted(
                [payload.source_warehouse_id, payload.target_warehouse_id], key=str
            )
            first_inventory = await self.repository.lock_inventory(
                cooperative_id, first, payload.batch_id
            )
            second_inventory = await self.repository.lock_inventory(
                cooperative_id, second, payload.batch_id
            )
            source = (
                first_inventory
                if first == payload.source_warehouse_id
                else second_inventory
            )
            target = (
                first_inventory
                if first == payload.target_warehouse_id
                else second_inventory
            )
            if source is None:
                raise InsufficientInventoryError(available=Decimal(0), requested=payload.quantity)
            if target is None:
                target = await self.repository.ensure_inventory_row(
                    cooperative_id, payload.target_warehouse_id, payload.batch_id
                )
            available = source.quantity - source.locked_quantity
            if payload.quantity > available:
                raise InsufficientInventoryError(
                    available=available, requested=payload.quantity
                )
            source_before = source.quantity
            target_before = target.quantity
            source_after = source_before - payload.quantity
            target_after = target_before + payload.quantity
            operation = await self.repository.add_operation(
                InventoryOperation(
                    cooperative_id=cooperative_id,
                    operation_no=self._new_operation_no(),
                    operation_type=InventoryOperationType.TRANSFER,
                    source_warehouse_id=payload.source_warehouse_id,
                    destination_warehouse_id=payload.target_warehouse_id,
                    reason=payload.remark,
                    occurred_at=payload.occurred_at,
                    status=InventoryOperationStatus.COMPLETED,
                    created_by=context.user_id,
                )
            )
            out_transaction = await self.repository.add_transaction(
                InventoryTransaction(
                    cooperative_id=cooperative_id,
                    operation_id=operation.id,
                    warehouse_id=payload.source_warehouse_id,
                    batch_id=batch.id,
                    transaction_type=InventoryTransactionType.TRANSFER_OUT,
                    quantity_delta=-payload.quantity,
                    quantity_before=source_before,
                    quantity_after=source_after,
                    occurred_at=payload.occurred_at,
                    created_by=context.user_id,
                )
            )
            in_transaction = await self.repository.add_transaction(
                InventoryTransaction(
                    cooperative_id=cooperative_id,
                    operation_id=operation.id,
                    warehouse_id=payload.target_warehouse_id,
                    batch_id=batch.id,
                    transaction_type=InventoryTransactionType.TRANSFER_IN,
                    quantity_delta=payload.quantity,
                    quantity_before=target_before,
                    quantity_after=target_after,
                    occurred_at=payload.occurred_at,
                    created_by=context.user_id,
                )
            )
            await self.repository.update_inventory(
                source, quantity=source_after, version=source.version + 1
            )
            await self.repository.update_inventory(
                target, quantity=target_after, version=target.version + 1
            )
            sync_batch_status(batch, source_after)
            data = TransferData(
                transfer_id=operation.id,
                out_transaction_id=out_transaction.id,
                in_transaction_id=in_transaction.id,
            ).model_dump(mode="json", by_alias=True)
            await self.idempotency.complete(
                context, cooperative_id, endpoint, idempotency_key, payload, data
            )
            return cast(dict[str, object], data)

    async def stocktake(
        self, context: AuthContext, payload: StocktakeCreate, idempotency_key: str
    ) -> dict[str, object]:
        require_write(context)
        cooperative_id = require_cooperative(context)
        endpoint = "/api/v1/stocktakes"
        async with transaction_scope(self.session):
            replay = await self.idempotency.prepare(
                context, cooperative_id, endpoint, idempotency_key, payload
            )
            if replay is not None:
                return replay
            await self._get_active_warehouse(context, cooperative_id, payload.warehouse_id)
            batch = await self._get_movable_batch(cooperative_id, payload.batch_id)
            inventory = await self.repository.ensure_inventory_row(
                cooperative_id, payload.warehouse_id, payload.batch_id
            )
            book_quantity = inventory.quantity
            difference = payload.counted_quantity - book_quantity
            if difference == 0:
                raise AppException(
                    code="NO_STOCKTAKE_ADJUSTMENT",
                    message="盘点数量与账面数量一致，无需生成调整流水",
                    status_code=400,
                )
            if payload.counted_quantity < inventory.locked_quantity:
                raise AppException(
                    code="QUANTITY_BELOW_LOCKED",
                    message="盘点数量不能低于锁定库存",
                    status_code=409,
                )
            operation = await self.repository.add_operation(
                InventoryOperation(
                    cooperative_id=cooperative_id,
                    operation_no=self._new_operation_no(),
                    operation_type=InventoryOperationType.ADJUSTMENT,
                    reason=payload.reason + (f"；{payload.remark}" if payload.remark else ""),
                    occurred_at=payload.occurred_at,
                    status=InventoryOperationStatus.COMPLETED,
                    created_by=context.user_id,
                )
            )
            transaction = await self.repository.add_transaction(
                InventoryTransaction(
                    cooperative_id=cooperative_id,
                    operation_id=operation.id,
                    warehouse_id=payload.warehouse_id,
                    batch_id=batch.id,
                    transaction_type=InventoryTransactionType.ADJUSTMENT,
                    quantity_delta=difference,
                    quantity_before=book_quantity,
                    quantity_after=payload.counted_quantity,
                    occurred_at=payload.occurred_at,
                    created_by=context.user_id,
                )
            )
            await self.repository.update_inventory(
                inventory,
                quantity=payload.counted_quantity,
                version=inventory.version + 1,
            )
            sync_batch_status(batch, payload.counted_quantity)
            data = StocktakeData(
                operation_id=operation.id,
                transaction_id=transaction.id,
                book_quantity=float(book_quantity),
                counted_quantity=float(payload.counted_quantity),
                difference_quantity=float(difference),
            ).model_dump(mode="json", by_alias=True)
            await self.idempotency.complete(
                context, cooperative_id, endpoint, idempotency_key, payload, data
            )
            return cast(dict[str, object], data)

    async def _change_single(
        self,
        context: AuthContext,
        payload: InventoryReceiptCreate | InventoryIssueCreate | InventoryLossCreate,
        idempotency_key: str,
        *,
        endpoint: str,
        operation_type: InventoryOperationType,
        transaction_type: InventoryTransactionType,
        quantity_delta: Decimal,
        reference_no: str | None,
        reason: str | None,
    ) -> dict[str, object]:
        require_write(context)
        cooperative_id = require_cooperative(context)
        async with transaction_scope(self.session):
            replay = await self.idempotency.prepare(
                context, cooperative_id, endpoint, idempotency_key, payload
            )
            if replay is not None:
                return replay
            warehouse_id = cast(UUID, payload.warehouse_id)
            batch_id = cast(UUID, payload.batch_id)
            await self._get_active_warehouse(context, cooperative_id, warehouse_id)
            batch = await self._get_movable_batch(cooperative_id, batch_id)
            inventory = await self.repository.ensure_inventory_row(
                cooperative_id, warehouse_id, batch_id
            )
            before = inventory.quantity
            available = before - inventory.locked_quantity
            if quantity_delta < 0 and -quantity_delta > available:
                raise InsufficientInventoryError(
                    available=available, requested=-quantity_delta
                )
            after = before + quantity_delta
            operation = await self.repository.add_operation(
                InventoryOperation(
                    cooperative_id=cooperative_id,
                    operation_no=self._new_operation_no(),
                    operation_type=operation_type,
                    external_reference=reference_no,
                    reason=reason,
                    occurred_at=payload.occurred_at,
                    status=InventoryOperationStatus.COMPLETED,
                    created_by=context.user_id,
                )
            )
            transaction = await self.repository.add_transaction(
                InventoryTransaction(
                    cooperative_id=cooperative_id,
                    operation_id=operation.id,
                    warehouse_id=warehouse_id,
                    batch_id=batch.id,
                    transaction_type=transaction_type,
                    quantity_delta=quantity_delta,
                    quantity_before=before,
                    quantity_after=after,
                    occurred_at=payload.occurred_at,
                    created_by=context.user_id,
                )
            )
            await self.repository.update_inventory(
                inventory, quantity=after, version=inventory.version + 1
            )
            sync_batch_status(batch, after)
            data = transaction_dict(transaction, operation.operation_no)
            await self.idempotency.complete(
                context, cooperative_id, endpoint, idempotency_key, payload, data
            )
            return data

    async def _get_active_warehouse(
        self, context: AuthContext, cooperative_id: UUID, warehouse_id: UUID
    ) -> Warehouse:
        if context.role_code == WAREHOUSE_STAFF_ROLE_CODE:
            ensure_warehouse_scope(context, warehouse_id)
        warehouse = await self.repository.get_warehouse(
            cooperative_id, warehouse_ids(context), warehouse_id
        )
        if warehouse is None:
            raise resource_not_found()
        if warehouse.status is not WarehouseStatus.ACTIVE:
            raise AppException(
                code="WAREHOUSE_INACTIVE", message="停用仓库不能进行库存操作", status_code=409
            )
        return warehouse

    async def _get_movable_batch(self, cooperative_id: UUID, batch_id: UUID) -> Batch:
        batch = await self.repository.get_batch(cooperative_id, batch_id)
        if batch is None:
            raise resource_not_found()
        if batch.status in {BatchStatus.BLOCKED, BatchStatus.EXPIRED}:
            raise StatusNotAllowedError(
                current_status=batch.status.value, allowed_statuses=[BatchStatus.IN_STOCK.value]
            )
        return batch

    @staticmethod
    def _new_operation_no() -> str:
        return f"OP-{uuid4().hex[:24]}"


__all__ = ["InventoryMutationService", "sync_batch_status"]
