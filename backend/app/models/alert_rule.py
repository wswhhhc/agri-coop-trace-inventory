from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, Uuid
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AlertSeverity, AlertType, enum_sql_values

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.cooperative import Cooperative
    from app.models.product import Product
    from app.models.warehouse import Warehouse


class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = (
        CheckConstraint(
            f"alert_type IN ({enum_sql_values(AlertType)})",
            name="ck_alert_rules_type",
        ),
        CheckConstraint(
            f"severity IN ({enum_sql_values(AlertSeverity)})",
            name="ck_alert_rules_severity",
        ),
        CheckConstraint(
            "threshold_quantity IS NULL OR threshold_quantity >= 0",
            name="ck_alert_rules_threshold_quantity",
        ),
        CheckConstraint(
            "threshold_days IS NULL OR threshold_days >= 0",
            name="ck_alert_rules_threshold_days",
        ),
        CheckConstraint(
            "turnover_days IS NULL OR turnover_days >= 0",
            name="ck_alert_rules_turnover_days",
        ),
        Index("ix_alert_rules_scope", "cooperative_id", "warehouse_id", "product_id", "alert_type"),
    )

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cooperatives.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT")
    )
    product_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT")
    )
    alert_type: Mapped[AlertType] = mapped_column(
        SqlEnum(AlertType, native_enum=False, create_constraint=False, name="ck_alert_rules_type", length=24),
        nullable=False,
    )
    threshold_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    threshold_days: Mapped[int | None] = mapped_column()
    turnover_days: Mapped[int | None] = mapped_column()
    severity: Mapped[AlertSeverity] = mapped_column(
        SqlEnum(AlertSeverity, native_enum=False, create_constraint=False, name="ck_alert_rules_severity", length=16),
        nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")

    cooperative: Mapped[Cooperative] = relationship("Cooperative")
    warehouse: Mapped[Warehouse | None] = relationship("Warehouse")
    product: Mapped[Product | None] = relationship("Product")
    alerts: Mapped[list[Alert]] = relationship("Alert", back_populates="rule")


__all__ = ["AlertRule"]
