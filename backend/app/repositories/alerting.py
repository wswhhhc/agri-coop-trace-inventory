from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, asc, desc, false, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models import (
    Alert,
    AlertHandlingLog,
    AlertRule,
    Batch,
    Inventory,
    QualityInspection,
)


class AlertingRepository:
    """预警规则、记录及处理日志的数据访问。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_rules(
        self, cooperative_id: UUID | None, *, page: int, page_size: int
    ) -> tuple[list[AlertRule], int]:
        conditions = self._cooperative_conditions(AlertRule, cooperative_id)
        total = await self.session.scalar(select(func.count(AlertRule.id)).where(*conditions))
        result = await self.session.scalars(
            select(AlertRule)
            .where(*conditions)
            .order_by(AlertRule.created_at, AlertRule.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def get_rule(self, cooperative_id: UUID | None, rule_id: UUID) -> AlertRule | None:
        return await self.session.scalar(
            select(AlertRule).where(
                AlertRule.id == rule_id,
                *self._cooperative_conditions(AlertRule, cooperative_id),
            )
        )

    async def list_alerts(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        alert_type,
        severity,
        status,
        warehouse_id: UUID | None,
        product_id: UUID | None,
        batch_id: UUID | None,
        created_after: datetime | None,
        created_before: datetime | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Alert], int]:
        conditions = self._alert_scope_conditions(cooperative_id, warehouse_ids)
        filters = {
            Alert.alert_type: alert_type,
            Alert.severity: severity,
            Alert.status: status,
            Alert.warehouse_id: warehouse_id,
            Alert.product_id: product_id,
            Alert.batch_id: batch_id,
        }
        conditions.extend(column == value for column, value in filters.items() if value is not None)
        if created_after is not None:
            conditions.append(Alert.created_at >= created_after)
        if created_before is not None:
            conditions.append(Alert.created_at <= created_before)
        statement: Select[tuple[Alert]] = (
            select(Alert)
            .options(selectinload(Alert.handling_logs))
            .where(*conditions)
        )
        total = await self.session.scalar(select(func.count(Alert.id)).where(*conditions))
        sort_column = {
            "detectedAt": Alert.detected_at,
            "detected_at": Alert.detected_at,
            "createdAt": Alert.created_at,
            "created_at": Alert.created_at,
            "severity": Alert.severity,
        }.get(sort_by, Alert.created_at)
        ordering = desc(sort_column) if sort_order == "DESC" else asc(sort_column)
        result = await self.session.scalars(
            statement.order_by(ordering, Alert.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), int(total or 0)

    async def get_alert(
        self, cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None, alert_id: UUID, *, lock: bool = False
    ) -> Alert | None:
        statement = (
            select(Alert)
            .options(selectinload(Alert.handling_logs))
            .where(Alert.id == alert_id, *self._alert_scope_conditions(cooperative_id, warehouse_ids))
        )
        if lock:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def add_alert(self, alert: Alert) -> Alert:
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def add_handling_log(self, log: AlertHandlingLog) -> AlertHandlingLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_enabled_rules(self, cooperative_id: UUID | None = None) -> list[AlertRule]:
        statement = select(AlertRule).where(AlertRule.is_enabled.is_(True))
        if cooperative_id is not None:
            statement = statement.where(AlertRule.cooperative_id == cooperative_id)
        result = await self.session.scalars(statement.order_by(AlertRule.id))
        return list(result)

    async def list_inventory_candidates(self, cooperative_id: UUID | None = None) -> list[Inventory]:
        statement = (
            select(Inventory)
            .join(Inventory.batch)
            .options(selectinload(Inventory.batch).selectinload(Batch.product))
        )
        if cooperative_id is not None:
            statement = statement.where(Inventory.cooperative_id == cooperative_id)
        result = await self.session.scalars(statement.order_by(Inventory.id))
        return list(result)

    async def list_failed_inspections(self, cooperative_id: UUID | None = None) -> list[QualityInspection]:
        statement = select(QualityInspection).where(QualityInspection.conclusion == "FAILED")
        if cooperative_id is not None:
            statement = statement.where(QualityInspection.cooperative_id == cooperative_id)
        result = await self.session.scalars(
            statement.order_by(QualityInspection.inspected_at.desc(), QualityInspection.id)
        )
        return list(result)

    async def get_active_by_dedupe(self, cooperative_id: UUID, dedupe_key: str) -> Alert | None:
        return await self.session.scalar(
            select(Alert).where(
                Alert.cooperative_id == cooperative_id,
                Alert.dedupe_key == dedupe_key,
                Alert.status.in_(("PENDING", "PROCESSING")),
            )
        )

    @staticmethod
    def _cooperative_conditions(model, cooperative_id: UUID | None) -> list[ColumnElement[bool]]:
        return [model.cooperative_id == cooperative_id] if cooperative_id is not None else []

    @staticmethod
    def _alert_scope_conditions(
        cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if cooperative_id is not None:
            conditions.append(Alert.cooperative_id == cooperative_id)
        if warehouse_ids is not None:
            conditions.append(false() if not warehouse_ids else Alert.warehouse_id.in_(warehouse_ids))
        return conditions


__all__ = ["AlertingRepository"]
