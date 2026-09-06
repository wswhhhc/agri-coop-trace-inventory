from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.models import AlertSeverity, AlertType
from app.services.alerting_engine import evaluate_inventory_rule, evaluate_quality_rule


def _rule(alert_type: AlertType, **kwargs):
    values = {
        "id": uuid4(),
        "alert_type": alert_type,
        "severity": AlertSeverity.HIGH,
        "threshold_quantity": None,
        "threshold_days": None,
        "turnover_days": None,
        "warehouse_id": None,
        "product_id": None,
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def _inventory(*, quantity="8", locked="1", safety="10", expiry=date(2026, 10, 1)):
    return SimpleNamespace(
        id=uuid4(), cooperative_id=uuid4(), warehouse_id=uuid4(), batch_id=uuid4(),
        quantity=Decimal(quantity), locked_quantity=Decimal(locked),
        batch=SimpleNamespace(expiry_date=expiry, product=SimpleNamespace(id=uuid4(), name="玉米", safety_stock=Decimal(safety))),
    )


def test_inventory_rules_return_evidence_only_when_triggered() -> None:
    inventory = _inventory()
    result = evaluate_inventory_rule(_rule(AlertType.LOW_STOCK, threshold_quantity=Decimal(10)), inventory, date(2026, 9, 6))
    assert result is not None
    assert result.alert_type is AlertType.LOW_STOCK
    assert result.evidence["availableQuantity"] == 7.0

    assert evaluate_inventory_rule(_rule(AlertType.LOW_STOCK, threshold_quantity=Decimal(5)), inventory, date(2026, 9, 6)) is None


def test_near_expiry_and_overstock_rules_use_configured_thresholds() -> None:
    near = _inventory(quantity="10", locked="0", expiry=date(2026, 9, 10))
    result = evaluate_inventory_rule(_rule(AlertType.NEAR_EXPIRY, threshold_days=5), near, date(2026, 9, 6))
    assert result is not None
    assert result.evidence["daysRemaining"] == 4

    over = _inventory(quantity="100", locked="0", safety="10")
    result = evaluate_inventory_rule(_rule(AlertType.OVERSTOCK, threshold_quantity=Decimal(90)), over, date(2026, 9, 6))
    assert result is not None
    assert result.evidence["quantity"] == 100.0


def test_quality_failed_rule_requires_failed_inspection() -> None:
    inspection = SimpleNamespace(
        id=uuid4(), batch_id=uuid4(), conclusion="FAILED", inspected_at=None,
    )
    result = evaluate_quality_rule(_rule(AlertType.QUALITY_FAILED), inspection)
    assert result is not None
    assert result.alert_type is AlertType.QUALITY_FAILED
    assert evaluate_quality_rule(_rule(AlertType.QUALITY_FAILED), SimpleNamespace(conclusion="PASSED")) is None


def test_scan_creates_each_active_dedupe_key_only_once(monkeypatch) -> None:
    from contextlib import asynccontextmanager

    from app.services.alerting import AlertingService

    cooperative_id = uuid4()
    inventory = _inventory(quantity="2", locked="0", safety="10")
    inventory.cooperative_id = cooperative_id
    rule = _rule(AlertType.LOW_STOCK, threshold_quantity=Decimal(5))
    rule.cooperative_id = cooperative_id
    created = []

    class FakeRepository:
        async def list_enabled_rules(self, cooperative_id=None):
            return [rule]

        async def list_inventory_candidates(self, cooperative_id=None):
            return [inventory]

        async def list_failed_inspections(self, cooperative_id=None):
            return []

        async def get_active_by_dedupe(self, cooperative_id, dedupe_key):
            return created[0] if created else None

        async def add_alert(self, alert):
            created.append(alert)
            return alert

    @asynccontextmanager
    async def no_transaction(session):
        yield

    monkeypatch.setattr("app.services.alerting.transaction_scope", no_transaction)
    service = AlertingService.__new__(AlertingService)
    service.session = object()
    service.repository = FakeRepository()

    import asyncio

    assert asyncio.run(service.scan(cooperative_id)) == 1
    assert asyncio.run(service.scan(cooperative_id)) == 0


def test_quality_integration_uses_current_transaction(monkeypatch) -> None:
    from app.services.alerting import AlertingQualityIntegration

    calls = []

    async def fake_create(self, inspection):
        calls.append(inspection)
        return 1

    monkeypatch.setattr("app.services.alerting.AlertingService.create_quality_alerts", fake_create)
    inspection = SimpleNamespace(id=uuid4())
    integration = AlertingQualityIntegration(object())

    import asyncio

    asyncio.run(integration.quality_failed(inspection))
    assert calls == [inspection]
