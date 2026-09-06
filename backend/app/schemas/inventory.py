from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from app.models.enums import (
    InventoryRisk,
    InventoryTransactionType,
)
from app.schemas.common import BaseSchema, PageParams


class InventoryListParams(PageParams):
    warehouse_id: UUID | None = None
    product_id: UUID | None = None
    batch_id: UUID | None = None
    stock_risk: InventoryRisk | None = None
    keyword: str | None = Field(default=None, max_length=100)


class InventoryTransactionListParams(PageParams):
    warehouse_id: UUID | None = None
    batch_id: UUID | None = None
    transaction_type: InventoryTransactionType | None = None
    occurred_at_from: AwareDatetime | None = None
    occurred_at_to: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_time_order(self) -> InventoryTransactionListParams:
        if (
            self.occurred_at_from is not None
            and self.occurred_at_to is not None
            and self.occurred_at_to < self.occurred_at_from
        ):
            raise ValueError("occurred_at_to 不能早于 occurred_at_from")
        return self


class InventoryReceiptCreate(BaseSchema):
    warehouse_id: UUID
    batch_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    occurred_at: AwareDatetime
    reference_no: str | None = Field(default=None, max_length=100)
    remark: str | None = Field(default=None, max_length=500)


class InventoryIssueCreate(BaseSchema):
    warehouse_id: UUID
    batch_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    occurred_at: AwareDatetime
    reference_no: str | None = Field(default=None, max_length=100)
    destination: str | None = Field(default=None, max_length=255)
    remark: str | None = Field(default=None, max_length=500)


class StockTransferCreate(BaseSchema):
    source_warehouse_id: UUID
    target_warehouse_id: UUID
    batch_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    occurred_at: AwareDatetime
    remark: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_warehouses(self) -> StockTransferCreate:
        if self.source_warehouse_id == self.target_warehouse_id:
            raise ValueError("source_warehouse_id 和 target_warehouse_id 不能相同")
        return self


class StocktakeCreate(BaseSchema):
    warehouse_id: UUID
    batch_id: UUID
    counted_quantity: Decimal = Field(ge=0, max_digits=14, decimal_places=3)
    occurred_at: AwareDatetime
    reason: str = Field(min_length=1, max_length=500)
    remark: str | None = Field(default=None, max_length=500)


class InventoryLossCreate(BaseSchema):
    warehouse_id: UUID
    batch_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    occurred_at: AwareDatetime
    reason: str = Field(min_length=1, max_length=500)
    remark: str | None = Field(default=None, max_length=500)


class WarehouseRef(BaseSchema):
    id: UUID
    name: str


class ProductRef(BaseSchema):
    id: UUID
    name: str
    unit: str


class BatchRef(BaseSchema):
    id: UUID
    batch_no: str
    expiry_date: date


class InventoryData(BaseSchema):
    id: UUID
    warehouse: WarehouseRef
    product: ProductRef
    batch: BatchRef
    quantity: float
    available_quantity: float
    risk_flags: list[InventoryRisk]
    updated_at: AwareDatetime


class InventoryTransactionData(BaseSchema):
    id: UUID
    transaction_id: UUID
    transaction_no: str
    operation_id: UUID
    operation_no: str
    transaction_type: InventoryTransactionType
    quantity: float
    quantity_delta: float
    quantity_before: float
    quantity_after: float
    warehouse_id: UUID
    batch_id: UUID
    occurred_at: AwareDatetime
    created_at: AwareDatetime


class TransferData(BaseSchema):
    transfer_id: UUID
    out_transaction_id: UUID
    in_transaction_id: UUID


class StocktakeData(BaseSchema):
    operation_id: UUID
    transaction_id: UUID
    book_quantity: float
    counted_quantity: float
    difference_quantity: float


__all__ = [
    "BatchRef",
    "InventoryData",
    "InventoryIssueCreate",
    "InventoryListParams",
    "InventoryLossCreate",
    "InventoryReceiptCreate",
    "InventoryTransactionData",
    "InventoryTransactionListParams",
    "ProductRef",
    "StockTransferCreate",
    "StocktakeCreate",
    "StocktakeData",
    "TransferData",
    "WarehouseRef",
]
