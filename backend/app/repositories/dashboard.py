from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import TypedDict, cast
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Alert,
    AlertStatus,
    Batch,
    ForecastResult,
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
    ModelVersion,
    Product,
)


class DashboardSummaryRaw(TypedDict):
    product_count: int
    batch_count: int
    inventory_by_unit: list[tuple[str, Decimal]]
    pending_alert_count: int
    expiring_batch_count: int
    low_stock_product_count: int


class DashboardRepository:
    """只读统计查询；不承载库存、预警或预测领域写规则。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        today: date,
    ) -> DashboardSummaryRaw:
        if warehouse_ids == frozenset():
            return {
                "product_count": 0,
                "batch_count": 0,
                "inventory_by_unit": [],
                "pending_alert_count": 0,
                "expiring_batch_count": 0,
                "low_stock_product_count": 0,
            }

        inventory_scope = self._inventory_scope(cooperative_id, warehouse_ids)
        product_scope = self._cooperative_scope(Product, cooperative_id)
        batch_scope = self._cooperative_scope(Batch, cooperative_id)
        alert_scope = self._alert_scope(cooperative_id, warehouse_ids)

        if warehouse_ids is None:
            product_count_statement = select(func.count(Product.id)).where(*product_scope)
            batch_count_statement = select(func.count(Batch.id)).where(*batch_scope)
        else:
            product_count_statement = (
                select(func.count(func.distinct(Product.id)))
                .select_from(Product)
                .join(Batch, Batch.product_id == Product.id)
                .join(Inventory, Inventory.batch_id == Batch.id)
                .where(*product_scope, *inventory_scope)
            )
            batch_count_statement = (
                select(func.count(func.distinct(Batch.id)))
                .select_from(Batch)
                .join(Inventory, Inventory.batch_id == Batch.id)
                .where(*batch_scope, *inventory_scope)
            )

        product_count = int(await self.session.scalar(product_count_statement) or 0)
        batch_count = int(await self.session.scalar(batch_count_statement) or 0)

        inventory_rows = await self.session.execute(
            select(Product.unit, func.coalesce(func.sum(Inventory.quantity), 0))
            .select_from(Inventory)
            .join(Batch, Batch.id == Inventory.batch_id)
            .join(Product, Product.id == Batch.product_id)
            .where(*inventory_scope)
            .group_by(Product.unit)
            .order_by(Product.unit)
        )

        pending_count = int(
            await self.session.scalar(
                select(func.count(Alert.id)).where(
                    *alert_scope,
                    Alert.status.in_((AlertStatus.PENDING, AlertStatus.PROCESSING)),
                )
            )
            or 0
        )

        expiring_scope = list(batch_scope)
        expiring_scope.extend(
            [Batch.expiry_date >= today, Batch.expiry_date <= today + timedelta(days=30)]
        )
        if warehouse_ids is not None:
            expiring_statement = (
                select(func.count(func.distinct(Batch.id)))
                .select_from(Batch)
                .join(Inventory, Inventory.batch_id == Batch.id)
                .where(*expiring_scope, *inventory_scope)
            )
        else:
            expiring_statement = select(func.count(Batch.id)).where(*expiring_scope)
        expiring_count = int(await self.session.scalar(expiring_statement) or 0)

        available_quantity = func.coalesce(
            func.sum(Inventory.quantity - Inventory.locked_quantity), 0
        )
        low_stock_statement = (
            select(Product.id)
            .select_from(Product)
            .outerjoin(Batch, Batch.product_id == Product.id)
            .outerjoin(
                Inventory,
                and_(Inventory.batch_id == Batch.id, *inventory_scope),
            )
            .where(*product_scope)
            .group_by(Product.id, Product.safety_stock)
            .having(available_quantity < Product.safety_stock)
            .subquery()
        )
        low_stock_count = int(
            await self.session.scalar(select(func.count()).select_from(low_stock_statement))
            or 0
        )

        return {
            "product_count": product_count,
            "batch_count": batch_count,
            "inventory_by_unit": [(row[0], row[1]) for row in inventory_rows.all()],
            "pending_alert_count": pending_count,
            "expiring_batch_count": expiring_count,
            "low_stock_product_count": low_stock_count,
        }

    async def inventory_trends(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        start_date: date,
        end_date: date,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[date, str, Decimal, Decimal, Decimal]], int]:
        if warehouse_ids == frozenset():
            return [], 0

        start_at = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
        scope = self._transaction_scope(cooperative_id, warehouse_ids)
        inbound_types = (InventoryTransactionType.INBOUND, InventoryTransactionType.TRANSFER_IN)
        outbound_types = (
            InventoryTransactionType.OUTBOUND,
            InventoryTransactionType.DAMAGE,
            InventoryTransactionType.TRANSFER_OUT,
        )
        day = func.date(InventoryTransaction.occurred_at).label("day")
        inbound = func.coalesce(
            func.sum(
                case(
                    (InventoryTransaction.transaction_type.in_(inbound_types), InventoryTransaction.quantity_delta),
                    else_=0,
                )
            ),
            0,
        ).label("inbound_quantity")
        outbound = func.coalesce(
            func.sum(
                case(
                    (InventoryTransaction.transaction_type.in_(outbound_types), -InventoryTransaction.quantity_delta),
                    else_=0,
                )
            ),
            0,
        ).label("outbound_quantity")
        net = func.coalesce(func.sum(InventoryTransaction.quantity_delta), 0).label("net_quantity")
        daily = (
            select(Product.unit.label("unit"), day, inbound, outbound, net)
            .select_from(InventoryTransaction)
            .join(Batch, Batch.id == InventoryTransaction.batch_id)
            .join(Product, Product.id == Batch.product_id)
            .where(
                *scope,
                InventoryTransaction.occurred_at >= start_at,
                InventoryTransaction.occurred_at < end_at,
            )
            .group_by(Product.unit, day)
            .cte("dashboard_daily_inventory")
        )
        opening = (
            select(
                Product.unit.label("unit"),
                func.coalesce(func.sum(InventoryTransaction.quantity_delta), 0).label("opening_quantity"),
            )
            .select_from(InventoryTransaction)
            .join(Batch, Batch.id == InventoryTransaction.batch_id)
            .join(Product, Product.id == Batch.product_id)
            .where(*scope, InventoryTransaction.occurred_at < start_at)
            .group_by(Product.unit)
            .cte("dashboard_opening_inventory")
        )
        running_net = func.sum(daily.c.net_quantity).over(
            partition_by=daily.c.unit,
            order_by=daily.c.day,
            rows=(None, 0),
        )
        statement = (
            select(
                daily.c.day,
                daily.c.unit,
                daily.c.inbound_quantity,
                daily.c.outbound_quantity,
                (func.coalesce(opening.c.opening_quantity, 0) + running_net).label("ending_quantity"),
            )
            .select_from(daily)
            .outerjoin(opening, opening.c.unit == daily.c.unit)
            .order_by(daily.c.day, daily.c.unit)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        total = await self.session.scalar(select(func.count()).select_from(daily))
        rows = await self.session.execute(statement)
        return [
            (row[0], row[1], row[2], row[3], row[4]) for row in rows.all()
        ], int(total or 0)

    async def alert_distribution(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        start_date: date,
        end_date: date,
    ) -> list[tuple[str, str, int]]:
        if warehouse_ids == frozenset():
            return []
        start_at = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
        rows = await self.session.execute(
            select(Alert.alert_type, Alert.severity, func.count(Alert.id))
            .where(
                *self._alert_scope(cooperative_id, warehouse_ids),
                Alert.detected_at >= start_at,
                Alert.detected_at < end_at,
            )
            .group_by(Alert.alert_type, Alert.severity)
            .order_by(Alert.alert_type, Alert.severity)
        )
        return [(str(row[0]), str(row[1]), int(row[2])) for row in rows.all()]

    async def product_ranking(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        start_date: date,
        end_date: date,
        limit: int,
    ) -> list[tuple[UUID, str, str, Decimal, int]]:
        if warehouse_ids == frozenset():
            return []
        start_at = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
        rows = await self.session.execute(
            select(
                Product.id,
                Product.name,
                Product.unit,
                func.sum(-InventoryTransaction.quantity_delta),
                func.count(InventoryTransaction.id),
            )
            .select_from(InventoryTransaction)
            .join(Batch, Batch.id == InventoryTransaction.batch_id)
            .join(Product, Product.id == Batch.product_id)
            .where(
                *self._transaction_scope(cooperative_id, warehouse_ids),
                InventoryTransaction.transaction_type == InventoryTransactionType.OUTBOUND,
                InventoryTransaction.occurred_at >= start_at,
                InventoryTransaction.occurred_at < end_at,
            )
            .group_by(Product.id, Product.name, Product.unit)
            .order_by(
                func.sum(-InventoryTransaction.quantity_delta).desc(),
                Product.id,
            )
            .limit(limit)
        )
        return [
            (row[0], row[1], row[2], row[3], int(row[4]))
            for row in rows.all()
        ]

    async def forecast_comparison(
        self,
        cooperative_id: UUID | None,
        warehouse_ids: frozenset[UUID] | None,
        *,
        start_date: date,
        end_date: date,
    ) -> list[tuple[UUID, UUID, UUID, UUID, str, date, date, Decimal, Decimal, dict[str, float]]]:
        if warehouse_ids == frozenset():
            return []
        start_at = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
        actual_demand = (
            select(func.coalesce(func.sum(-InventoryTransaction.quantity_delta), 0))
            .select_from(InventoryTransaction)
            .join(Batch, Batch.id == InventoryTransaction.batch_id)
            .where(
                InventoryTransaction.cooperative_id == ForecastResult.cooperative_id,
                InventoryTransaction.warehouse_id == ForecastResult.warehouse_id,
                Batch.product_id == ForecastResult.product_id,
                InventoryTransaction.transaction_type == InventoryTransactionType.OUTBOUND,
                InventoryTransaction.occurred_at >= ForecastResult.forecast_start_date,
                InventoryTransaction.occurred_at
                < ForecastResult.forecast_end_date + timedelta(days=1),
            )
            .correlate(ForecastResult)
            .scalar_subquery()
        )
        rows = await self.session.execute(
            select(
                ForecastResult.id,
                ForecastResult.warehouse_id,
                ForecastResult.product_id,
                ForecastResult.model_version_id,
                ModelVersion.version,
                ForecastResult.forecast_start_date,
                ForecastResult.forecast_end_date,
                ForecastResult.predicted_demand,
                actual_demand,
                ForecastResult.metrics,
            )
            .select_from(ForecastResult)
            .join(ModelVersion, ModelVersion.id == ForecastResult.model_version_id)
            .where(
                *self._forecast_scope(cooperative_id, warehouse_ids),
                ForecastResult.generated_at >= start_at,
                ForecastResult.generated_at < end_at,
            )
            .order_by(ForecastResult.generated_at.desc(), ForecastResult.id)
        )
        return [
            (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
                cast(Decimal, row[7]),
                cast(Decimal, row[8]),
                cast(dict[str, float], row[9]),
            )
            for row in rows.all()
        ]

    @staticmethod
    def _cooperative_scope(model, cooperative_id: UUID | None):
        return [model.cooperative_id == cooperative_id] if cooperative_id is not None else []

    @staticmethod
    def _inventory_scope(
        cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None
    ):
        conditions = DashboardRepository._cooperative_scope(Inventory, cooperative_id)
        if warehouse_ids is not None:
            conditions.append(Inventory.warehouse_id.in_(warehouse_ids))
        return conditions

    @staticmethod
    def _transaction_scope(
        cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None
    ):
        conditions = DashboardRepository._cooperative_scope(
            InventoryTransaction, cooperative_id
        )
        if warehouse_ids is not None:
            conditions.append(InventoryTransaction.warehouse_id.in_(warehouse_ids))
        return conditions

    @staticmethod
    def _alert_scope(
        cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None
    ):
        conditions = DashboardRepository._cooperative_scope(Alert, cooperative_id)
        if warehouse_ids is not None:
            conditions.append(Alert.warehouse_id.in_(warehouse_ids))
        return conditions

    @staticmethod
    def _forecast_scope(
        cooperative_id: UUID | None, warehouse_ids: frozenset[UUID] | None
    ):
        conditions = DashboardRepository._cooperative_scope(ForecastResult, cooperative_id)
        if warehouse_ids is not None:
            conditions.append(ForecastResult.warehouse_id.in_(warehouse_ids))
        return conditions


__all__ = ["DashboardRepository", "DashboardSummaryRaw"]
