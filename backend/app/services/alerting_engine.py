from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.models import AlertSeverity, AlertType


@dataclass(frozen=True, slots=True)
class AlertEvaluation:
    alert_type: AlertType
    severity: AlertSeverity
    warehouse_id: UUID | None
    product_id: UUID | None
    batch_id: UUID | None
    dedupe_key: str
    title: str
    message: str
    evidence: dict[str, object]


def evaluate_inventory_rule(rule, inventory, today: date) -> AlertEvaluation | None:
    available = Decimal(inventory.quantity) - Decimal(inventory.locked_quantity)
    alert_type = rule.alert_type
    evidence: dict[str, object]
    triggered = False
    if alert_type is AlertType.LOW_STOCK:
        threshold = rule.threshold_quantity
        if threshold is None:
            threshold = inventory.batch.product.safety_stock
        triggered = available < Decimal(threshold)
        evidence = {"availableQuantity": float(available), "thresholdQuantity": float(threshold)}
        message = f"当前可用库存{available:g}，低于阈值{Decimal(threshold):g}"
    elif alert_type is AlertType.NEAR_EXPIRY:
        threshold_days = int(rule.threshold_days or 30)
        days_remaining = (inventory.batch.expiry_date - today).days
        triggered = 0 <= days_remaining <= threshold_days and available > 0
        evidence = {"expiryDate": inventory.batch.expiry_date.isoformat(), "daysRemaining": days_remaining, "thresholdDays": threshold_days}
        message = f"批次将在{days_remaining}天后到期"
    elif alert_type is AlertType.OVERSTOCK:
        threshold = rule.threshold_quantity
        if threshold is None:
            threshold = Decimal(inventory.batch.product.safety_stock) * 10
        days_in_stock = max(0, (today - inventory.batch.production_date).days)
        turnover_days = rule.turnover_days
        triggered = available >= Decimal(threshold) and (
            turnover_days is None or days_in_stock >= turnover_days
        )
        evidence = {
            "quantity": float(available),
            "thresholdQuantity": float(threshold),
            "daysInStock": days_in_stock,
            "turnoverDays": turnover_days,
        }
        message = f"当前可用库存{available:g}，达到积压阈值{Decimal(threshold):g}"
    else:
        return None
    if not triggered:
        return None
    product = inventory.batch.product
    return AlertEvaluation(
        alert_type=alert_type,
        severity=rule.severity,
        warehouse_id=inventory.warehouse_id,
        product_id=product.id,
        batch_id=inventory.batch_id,
        dedupe_key=f"{alert_type.value}:{inventory.warehouse_id}:{inventory.batch_id}",
        title=f"{product.name}{_title_suffix(alert_type)}",
        message=message,
        evidence=evidence,
    )


def evaluate_quality_rule(rule, inspection) -> AlertEvaluation | None:
    if rule.alert_type is not AlertType.QUALITY_FAILED or inspection.conclusion != "FAILED":
        return None
    return AlertEvaluation(
        alert_type=AlertType.QUALITY_FAILED,
        severity=rule.severity,
        warehouse_id=None,
        product_id=None,
        batch_id=inspection.batch_id,
        dedupe_key=f"QUALITY_FAILED:{inspection.batch_id}",
        title="批次质检不合格",
        message="批次最新质检结论为不合格，请暂停出库并复核",
        evidence={"inspectionId": str(inspection.id), "conclusion": "FAILED"},
    )


def _title_suffix(alert_type: AlertType) -> str:
    return {
        AlertType.LOW_STOCK: "库存不足",
        AlertType.NEAR_EXPIRY: "临期",
        AlertType.OVERSTOCK: "库存积压",
    }[alert_type]


__all__ = ["AlertEvaluation", "evaluate_inventory_rule", "evaluate_quality_rule"]
