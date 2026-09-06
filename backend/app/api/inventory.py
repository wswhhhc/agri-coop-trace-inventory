from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.api.traceability import get_traceability_cache
from app.core.auth.dependencies import CurrentAuthContext
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

router = APIRouter(tags=["inventory"])


def get_inventory_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    cache: Annotated[TraceabilityCache, Depends(get_traceability_cache)],
) -> InventoryService:
    return InventoryService(session, cache)


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
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ApiResponse[InventoryTransactionData]:
    data = await service.receive(context, payload, idempotency_key)
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
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ApiResponse[InventoryTransactionData]:
    data = await service.issue(context, payload, idempotency_key)
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
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ApiResponse[TransferData]:
    data = await service.transfer(context, payload, idempotency_key)
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
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ApiResponse[StocktakeData]:
    data = await service.stocktake(context, payload, idempotency_key)
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
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ApiResponse[InventoryTransactionData]:
    data = await service.loss(context, payload, idempotency_key)
    return ApiResponse(data=InventoryTransactionData.model_validate(data))


__all__ = ["get_inventory_service", "router"]
