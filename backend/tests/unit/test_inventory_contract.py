from __future__ import annotations

from uuid import uuid4

import pytest
from app.core.config import Settings
from app.main import create_app
from app.schemas.inventory import InventoryReceiptCreate, StockTransferCreate
from pydantic import ValidationError


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
    )


def test_inventory_payload_rejects_non_positive_quantity() -> None:
    with pytest.raises(ValidationError):
        InventoryReceiptCreate(
            warehouse_id=uuid4(),
            batch_id=uuid4(),
            quantity=0,
            occurred_at="2026-09-06T10:00:00+08:00",
        )


def test_transfer_payload_rejects_same_source_and_target() -> None:
    warehouse_id = uuid4()
    with pytest.raises(ValidationError):
        StockTransferCreate(
            source_warehouse_id=warehouse_id,
            target_warehouse_id=warehouse_id,
            batch_id=uuid4(),
            quantity=1,
            occurred_at="2026-09-06T10:00:00+08:00",
        )


def test_inventory_routes_are_registered() -> None:
    paths = set(create_app(_settings()).openapi()["paths"])
    assert {
        "/api/v1/inventories",
        "/api/v1/inventory-transactions",
        "/api/v1/inventory-transactions/{transactionId}",
        "/api/v1/inventory-receipts",
        "/api/v1/inventory-issues",
        "/api/v1/stock-transfers",
        "/api/v1/stocktakes",
        "/api/v1/inventory-losses",
    } <= paths
