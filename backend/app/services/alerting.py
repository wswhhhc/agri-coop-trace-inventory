from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import resource_not_found
from app.core.auth.context import AuthContext
from app.core.exceptions import StatusNotAllowedError
from app.core.validation import require_non_empty_update
from app.infrastructure.transaction import transaction_scope
from app.models import (
    Alert,
    AlertHandlingLog,
    AlertRule,
    AlertStatus,
    AlertType,
    QualityInspection,
    TaskRecord,
    TaskStatus,
)
from app.repositories.alerting import AlertingRepository
from app.schemas.alerting import AlertListParams, AlertRuleUpdate, AlertStatusUpdate
from app.services.alerting_engine import evaluate_inventory_rule, evaluate_quality_rule
from app.services.alerting_policy import (
    require_alert_handle,
    require_alert_read,
    require_rule_manage,
    require_scan_submit,
    warehouse_ids_for_query,
)

_ALLOWED_STATUS_TRANSITIONS: dict[AlertStatus, frozenset[AlertStatus]] = {
    AlertStatus.PENDING: frozenset({AlertStatus.PROCESSING, AlertStatus.RESOLVED, AlertStatus.IGNORED}),
    AlertStatus.PROCESSING: frozenset({AlertStatus.RESOLVED, AlertStatus.IGNORED}),
    AlertStatus.RESOLVED: frozenset(),
    AlertStatus.IGNORED: frozenset(),
}


def allowed_status_transitions(status: AlertStatus) -> set[AlertStatus]:
    return set(_ALLOWED_STATUS_TRANSITIONS[status])


class AlertingService:
    """规则管理、预警查询和状态处理用例。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AlertingRepository(session)

    async def list_rules(self, context: AuthContext, page: int, page_size: int) -> tuple[list[AlertRule], int]:
        require_rule_manage(context)
        async with transaction_scope(self.session):
            return await self.repository.list_rules(context.cooperative_id, page=page, page_size=page_size)

    async def update_rule(self, context: AuthContext, rule_id: UUID, payload: AlertRuleUpdate) -> AlertRule:
        require_rule_manage(context)
        async with transaction_scope(self.session):
            rule = await self.repository.get_rule(context.cooperative_id, rule_id)
            if rule is None:
                raise resource_not_found()
            values = require_non_empty_update(payload.model_dump(exclude_unset=True))
            for key, value in values.items():
                setattr(rule, key, value)
            await self.session.flush()
            return rule

    async def list_alerts(self, context: AuthContext, params: AlertListParams) -> tuple[list[Alert], int]:
        require_alert_read(context)
        if params.warehouse_id is not None and not context.has_warehouse_access(params.warehouse_id):
            raise resource_not_found()
        async with transaction_scope(self.session):
            return await self.repository.list_alerts(
                context.cooperative_id,
                warehouse_ids_for_query(context),
                alert_type=params.type,
                severity=params.severity,
                status=params.status,
                warehouse_id=params.warehouse_id,
                product_id=params.product_id,
                batch_id=params.batch_id,
                created_after=params.created_after,
                created_before=params.created_before,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order.value,
            )

    async def get_alert(self, context: AuthContext, alert_id: UUID) -> Alert:
        require_alert_read(context)
        async with transaction_scope(self.session):
            alert = await self.repository.get_alert(context.cooperative_id, warehouse_ids_for_query(context), alert_id)
            if alert is None:
                raise resource_not_found()
            return alert

    async def update_alert(self, context: AuthContext, alert_id: UUID, payload: AlertStatusUpdate) -> Alert:
        require_alert_handle(context)
        async with transaction_scope(self.session):
            alert = await self.repository.get_alert(
                context.cooperative_id, warehouse_ids_for_query(context), alert_id, lock=True
            )
            if alert is None:
                raise resource_not_found()
            if payload.status == alert.status:
                raise StatusNotAllowedError(
                    current_status=alert.status.value,
                    allowed_statuses=sorted(status.value for status in _ALLOWED_STATUS_TRANSITIONS[alert.status]),
                )
            if payload.status not in _ALLOWED_STATUS_TRANSITIONS[alert.status]:
                raise StatusNotAllowedError(
                    current_status=alert.status.value,
                    allowed_statuses=sorted(status.value for status in _ALLOWED_STATUS_TRANSITIONS[alert.status]),
                )
            previous_status = alert.status
            alert.status = payload.status
            alert.assignee_id = context.user_id
            alert.resolved_at = datetime.now(UTC) if payload.status in {AlertStatus.RESOLVED, AlertStatus.IGNORED} else None
            await self.session.flush()
            await self.repository.add_handling_log(
                AlertHandlingLog(
                    alert_id=alert.id,
                    operator_id=context.user_id,
                    from_status=previous_status,
                    to_status=payload.status,
                    comment=payload.handling_note,
                )
            )
            return alert

    async def scan(self, cooperative_id: UUID | None = None) -> int:
        """扫描启用规则并创建活动预警；重复扫描对活动预警保持幂等。"""
        created_count = 0
        async with transaction_scope(self.session):
            rules = await self.repository.list_enabled_rules(cooperative_id)
            inventories = await self.repository.list_inventory_candidates(cooperative_id)
            failed_inspections = await self.repository.list_failed_inspections(cooperative_id)
            latest_failed: dict[UUID, QualityInspection] = {}
            for inspection in failed_inspections:
                latest_failed.setdefault(inspection.batch_id, inspection)
            for rule in rules:
                evaluations = []
                if rule.alert_type in {AlertType.LOW_STOCK, AlertType.NEAR_EXPIRY, AlertType.OVERSTOCK}:
                    for inventory in inventories:
                        if not _rule_matches_inventory(rule, inventory):
                            continue
                        if (evaluation := evaluate_inventory_rule(rule, inventory, datetime.now(UTC).date())) is not None:
                            evaluations.append((inventory.cooperative_id, evaluation))
                elif rule.alert_type is AlertType.QUALITY_FAILED:
                    for inspection in latest_failed.values():
                        if rule.cooperative_id != inspection.cooperative_id:
                            continue
                        if (evaluation := evaluate_quality_rule(rule, inspection)) is not None:
                            evaluations.append((inspection.cooperative_id, evaluation))
                for current_cooperative_id, evaluation in evaluations:
                    if await self.repository.get_active_by_dedupe(current_cooperative_id, evaluation.dedupe_key):
                        continue
                    await self.repository.add_alert(
                        Alert(
                            cooperative_id=current_cooperative_id,
                            rule_id=rule.id,
                            alert_type=evaluation.alert_type,
                            severity=evaluation.severity,
                            status=AlertStatus.PENDING,
                            warehouse_id=evaluation.warehouse_id,
                            product_id=evaluation.product_id,
                            batch_id=evaluation.batch_id,
                            dedupe_key=evaluation.dedupe_key,
                            title=evaluation.title,
                            message=evaluation.message,
                            evidence=evaluation.evidence,
                            detected_at=datetime.now(UTC),
                        )
                    )
                    created_count += 1
        return created_count

    async def submit_scan(self, context: AuthContext, enqueue: Callable[..., object]) -> TaskRecord:
        require_scan_submit(context)
        celery_task_id = str(uuid4())
        async with transaction_scope(self.session):
            record = TaskRecord(
                cooperative_id=context.cooperative_id,
                task_type="ALERT_SCAN",
                celery_task_id=celery_task_id,
                status=TaskStatus.PENDING,
                requested_by=context.user_id,
                request_payload={"cooperativeId": str(context.cooperative_id) if context.cooperative_id else None},
            )
            self.session.add(record)
            await self.session.flush()
        try:
            enqueue(
                args=[str(context.cooperative_id)] if context.cooperative_id else [],
                kwargs={"task_record_id": str(record.id)},
                task_id=celery_task_id,
            )
        except Exception as error:
            async with transaction_scope(self.session):
                failed = await self.session.get(TaskRecord, record.id, with_for_update=True)
                if failed is not None:
                    failed.status = TaskStatus.FAILURE
                    failed.error_code = "TASK_SUBMIT_FAILED"
                    failed.error_message = str(error)[:500]
            raise
        return record

    async def create_quality_alerts(self, inspection: QualityInspection) -> int:
        """在质检所属事务内追加不合格预警，不自行提交事务。"""
        created_count = 0
        rules = await self.repository.list_enabled_rules(inspection.cooperative_id)
        for rule in rules:
            if rule.alert_type is not AlertType.QUALITY_FAILED:
                continue
            evaluation = evaluate_quality_rule(rule, inspection)
            if evaluation is None or await self.repository.get_active_by_dedupe(
                inspection.cooperative_id, evaluation.dedupe_key
            ):
                continue
            await self.repository.add_alert(
                Alert(
                    cooperative_id=inspection.cooperative_id,
                    rule_id=rule.id,
                    alert_type=evaluation.alert_type,
                    severity=evaluation.severity,
                    status=AlertStatus.PENDING,
                    batch_id=evaluation.batch_id,
                    dedupe_key=evaluation.dedupe_key,
                    title=evaluation.title,
                    message=evaluation.message,
                    evidence=evaluation.evidence,
                    detected_at=inspection.inspected_at,
                )
            )
            created_count += 1
        return created_count


def _rule_matches_inventory(rule: AlertRule, inventory) -> bool:
    if rule.cooperative_id != inventory.cooperative_id:
        return False
    if rule.warehouse_id is not None and rule.warehouse_id != inventory.warehouse_id:
        return False
    return rule.product_id is None or rule.product_id == inventory.batch.product_id


class AlertingQualityIntegration:
    """质检事务内的预警适配器。"""

    def __init__(self, session: AsyncSession) -> None:
        self.service = AlertingService(session)

    async def inspection_created(self, inspection: QualityInspection) -> None:
        return None

    async def quality_failed(self, inspection: QualityInspection) -> None:
        await self.service.create_quality_alerts(inspection)


__all__ = [
    "AlertingQualityIntegration",
    "AlertingService",
    "allowed_status_transitions",
]
