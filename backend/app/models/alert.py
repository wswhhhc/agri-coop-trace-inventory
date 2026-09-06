from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid, text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AlertSeverity, AlertStatus, AlertType, enum_sql_values

if TYPE_CHECKING:
    from app.models.alert_handling_log import AlertHandlingLog
    from app.models.alert_rule import AlertRule
    from app.models.batch import Batch
    from app.models.cooperative import Cooperative
    from app.models.product import Product
    from app.models.user import User
    from app.models.warehouse import Warehouse


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint(
            f"alert_type IN ({enum_sql_values(AlertType)})", name="ck_alerts_type"
        ),
        CheckConstraint(
            f"severity IN ({enum_sql_values(AlertSeverity)})", name="ck_alerts_severity"
        ),
        CheckConstraint(
            f"status IN ({enum_sql_values(AlertStatus)})", name="ck_alerts_status"
        ),
        CheckConstraint(
            "(status IN ('PENDING', 'PROCESSING') AND resolved_at IS NULL) "
            "OR (status IN ('RESOLVED', 'IGNORED') AND resolved_at IS NOT NULL)",
            name="ck_alerts_resolution_time",
        ),
        Index("uq_alerts_active_dedupe", "cooperative_id", "dedupe_key", unique=True, postgresql_where=text("status IN ('PENDING', 'PROCESSING')")),
        Index("ix_alerts_workbench", "cooperative_id", "status", "severity", text("detected_at DESC")),
    )

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cooperatives.id", ondelete="RESTRICT"), nullable=False
    )
    rule_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("alert_rules.id", ondelete="SET NULL")
    )
    alert_type: Mapped[AlertType] = mapped_column(
        SqlEnum(AlertType, native_enum=False, create_constraint=False, name="ck_alerts_type", length=24), nullable=False
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        SqlEnum(AlertSeverity, native_enum=False, create_constraint=False, name="ck_alerts_severity", length=16), nullable=False
    )
    status: Mapped[AlertStatus] = mapped_column(
        SqlEnum(AlertStatus, native_enum=False, create_constraint=False, name="ck_alerts_status", length=16),
        nullable=False, default=AlertStatus.PENDING, server_default=AlertStatus.PENDING.value,
    )
    warehouse_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"))
    product_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"))
    batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("batches.id", ondelete="RESTRICT"))
    dedupe_key: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assignee_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    cooperative: Mapped[Cooperative] = relationship("Cooperative")
    rule: Mapped[AlertRule | None] = relationship("AlertRule", back_populates="alerts")
    warehouse: Mapped[Warehouse | None] = relationship("Warehouse")
    product: Mapped[Product | None] = relationship("Product")
    batch: Mapped[Batch | None] = relationship("Batch")
    assignee: Mapped[User | None] = relationship("User")
    handling_logs: Mapped[list[AlertHandlingLog]] = relationship("AlertHandlingLog", back_populates="alert", order_by="AlertHandlingLog.created_at")


__all__ = ["Alert"]
