from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models import Batch, BatchStatus, Product
from app.schemas.inventory import InventoryReceiptCreate
from app.services.inventory_idempotency import request_hash_for
from app.services.inventory_mutations import sync_batch_status


def test_inventory_request_hash_is_stable_for_the_same_payload() -> None:
    payload = InventoryReceiptCreate(
        warehouse_id="11111111-1111-1111-1111-111111111111",
        batch_id="22222222-2222-2222-2222-222222222222",
        quantity=Decimal("1.250"),
        occurred_at="2026-09-06T10:00:00+08:00",
    )
    assert request_hash_for(payload) == request_hash_for(payload)


def test_sync_batch_status_tracks_whether_inventory_is_zero() -> None:
    product = Product(
        cooperative_id="11111111-1111-1111-1111-111111111111",
        category_id="22222222-2222-2222-2222-222222222222",
        code="corn",
        name="玉米",
        unit="KG",
        shelf_life_days=365,
        safety_stock=Decimal(10),
    )
    batch = Batch(
        cooperative_id="11111111-1111-1111-1111-111111111111",
        product=product,
        batch_no="B-001",
        trace_code="T-001",
        origin="测试基地",
        production_date=date(2026, 9, 1),
        expiry_date=date(2027, 9, 1),
        status=BatchStatus.CREATED,
        created_by="33333333-3333-3333-3333-333333333333",
    )
    sync_batch_status(batch, Decimal(5))
    assert batch.status is BatchStatus.IN_STOCK
    sync_batch_status(batch, Decimal(0))
    assert batch.status is BatchStatus.DEPLETED
