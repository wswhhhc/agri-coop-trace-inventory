from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.api.traceability import get_traceability_cache
from app.core.audit.service import (
    AuditEvent,
    AuditLogService,
    audit_error_code,
    record_audit_safely,
)
from app.core.auth.dependencies import CurrentAuthContext, get_audit_log_service
from app.infrastructure.database import get_db_session
from app.schemas.common import ApiResponse, ListResponse
from app.schemas.inventory import (
    InventoryData,
    InventoryIssueCreate,
    InventoryListParams,
    InventoryLossCreate,
    InventoryReceiptCreate,
    InventoryTransactionData,
    InventoryTransactionListParams,
    StocktakeCreate,
    StocktakeData,
    StockTransferCreate,
    TransferData,
)
from app.services.inventory import InventoryService
from app.services.inventory_presenter import inventory_data, transaction_data
from app.services.traceability import TraceabilityCache
from app.tasks.alerting_tasks import scan_alerts_task

router = APIRouter(tags=["inventory"])
logger = logging.getLogger(__name__)


def get_inventory_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cache: Annotated[TraceabilityCache, Depends(get_traceability_cache)],
) -> InventoryService:
    return InventoryService(session, cache, scan_alerts_task.apply_async)


@router.get("/inventories", response_model=ListResponse[InventoryData])
async def list_inventories(
    params: Annotated[InventoryListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ListResponse[InventoryData]:
    items, total = await service.list_current(context, params)
    return ListResponse(
        data=[inventory_data(item) for item in items],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@router.get(
    "/inventory-transactions",
    response_model=ListResponse[InventoryTransactionData],
)
async def list_inventory_transactions(
    params: Annotated[InventoryTransactionListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ListResponse[InventoryTransactionData]:
    items, total = await service.list_transactions(context, params)
    return ListResponse(
        data=[transaction_data(item) for item in items],
        pagination=build_pagination_meta(total, params.page, params.page_size),
    )


@router.get(
    "/inventory-transactions/{transactionId}",
    response_model=ApiResponse[InventoryTransactionData],
)
async def get_inventory_transaction(
    transaction_id: Annotated[UUID, Path(alias="transactionId")],
    context: CurrentAuthContext,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ApiResponse[InventoryTransactionData]:
    return ApiResponse(data=transaction_data(await service.get_transaction(context, transaction_id)))


@router.post(
    "/inventory-receipts",
    response_model=ApiResponse[InventoryTransactionData],
    status_code=201,
)
async def create_inventory_receipt(
    payload: InventoryReceiptCreate,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[InventoryTransactionData]:
    data = await _execute_with_audit(
        lambda: service.receive(context, payload, idempotency_key),
        context=context,
        request=request,
        audit_log_service=audit_log_service,
        action="INVENTORY_RECEIPT",
        object_type="INVENTORY_TRANSACTION",
        object_id_key="transactionId",
        detail={
            "warehouseId": str(payload.warehouse_id),
            "batchId": str(payload.batch_id),
        },
    )
    return ApiResponse(data=InventoryTransactionData.model_validate(data))


@router.post(
    "/inventory-issues",
    response_model=ApiResponse[InventoryTransactionData],
    status_code=201,
)
async def create_inventory_issue(
    payload: InventoryIssueCreate,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[InventoryTransactionData]:
    data = await _execute_with_audit(
        lambda: service.issue(context, payload, idempotency_key),
        context=context,
        request=request,
        audit_log_service=audit_log_service,
        action="INVENTORY_ISSUE",
        object_type="INVENTORY_TRANSACTION",
        object_id_key="transactionId",
        detail={
            "warehouseId": str(payload.warehouse_id),
            "batchId": str(payload.batch_id),
        },
    )
    return ApiResponse(data=InventoryTransactionData.model_validate(data))


@router.post(
    "/stock-transfers",
    response_model=ApiResponse[TransferData],
    status_code=201,
)
async def create_stock_transfer(
    payload: StockTransferCreate,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[TransferData]:
    data = await _execute_with_audit(
        lambda: service.transfer(context, payload, idempotency_key),
        context=context,
        request=request,
        audit_log_service=audit_log_service,
        action="STOCK_TRANSFER",
        object_type="INVENTORY_OPERATION",
        object_id_key="transferId",
        detail={
            "sourceWarehouseId": str(payload.source_warehouse_id),
            "targetWarehouseId": str(payload.target_warehouse_id),
            "batchId": str(payload.batch_id),
        },
    )
    return ApiResponse(data=TransferData.model_validate(data))


@router.post(
    "/stocktakes",
    response_model=ApiResponse[StocktakeData],
    status_code=201,
)
async def create_stocktake(
    payload: StocktakeCreate,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[StocktakeData]:
    data = await _execute_with_audit(
        lambda: service.stocktake(context, payload, idempotency_key),
        context=context,
        request=request,
        audit_log_service=audit_log_service,
        action="STOCKTAKE",
        object_type="INVENTORY_TRANSACTION",
        object_id_key="transactionId",
        detail={
            "warehouseId": str(payload.warehouse_id),
            "batchId": str(payload.batch_id),
        },
    )
    return ApiResponse(data=StocktakeData.model_validate(data))


@router.post(
    "/inventory-losses",
    response_model=ApiResponse[InventoryTransactionData],
    status_code=201,
)
async def create_inventory_loss(
    payload: InventoryLossCreate,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    context: CurrentAuthContext,
    request: Request,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    audit_log_service: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> ApiResponse[InventoryTransactionData]:
    data = await _execute_with_audit(
        lambda: service.loss(context, payload, idempotency_key),
        context=context,
        request=request,
        audit_log_service=audit_log_service,
        action="INVENTORY_LOSS",
        object_type="INVENTORY_TRANSACTION",
        object_id_key="transactionId",
        detail={
            "warehouseId": str(payload.warehouse_id),
            "batchId": str(payload.batch_id),
        },
    )
    return ApiResponse(data=InventoryTransactionData.model_validate(data))


async def _execute_with_audit(
    operation: Callable[[], Awaitable[dict[str, object]]],
    *,
    context,
    request: Request,
    audit_log_service: AuditLogService,
    action: str,
    object_type: str,
    object_id_key: str,
    detail: dict[str, object],
) -> dict[str, object]:
    try:
        data = await operation()
    except Exception as error:
        await _record_inventory_audit(
            audit_log_service,
            request,
            context,
            action=action,
            object_type=object_type,
            result="FAILURE",
            detail={**detail, "errorCode": audit_error_code(error)},
        )
        raise
    await _record_inventory_audit(
        audit_log_service,
        request,
        context,
        action=action,
        object_type=object_type,
        result="SUCCESS",
        object_id=_uuid_from_result(data.get(object_id_key)),
        detail={**detail, **_result_detail(data)},
    )
    return data


async def _record_inventory_audit(
    audit_log_service: AuditLogService,
    request: Request,
    context,
    *,
    action: str,
    object_type: str,
    result: str,
    detail: dict[str, object],
    object_id: UUID | None = None,
) -> None:
    await record_audit_safely(
        audit_log_service,
        AuditEvent(
            action=action,
            module="INVENTORY",
            object_type=object_type,
            result=result,
            cooperative_id=context.cooperative_id,
            user_id=context.user_id,
            object_id=object_id,
            request_id=getattr(request.state, "request_id", None),
            detail=detail,
        ),
        logger,
    )


def _uuid_from_result(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            return None
    return None


def _result_detail(data: dict[str, object]) -> dict[str, object]:
    keys = (
        "operationNo",
        "transactionNo",
        "quantity",
        "quantityDelta",
        "quantityBefore",
        "quantityAfter",
        "differenceQuantity",
    )
    return {key: data[key] for key in keys if key in data}


__all__ = ["get_inventory_service", "router"]
