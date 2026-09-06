from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DataType, enum_sql_values

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.forecast_point import ForecastPoint
    from app.models.model_version import ModelVersion
    from app.models.product import Product
    from app.models.task_record import TaskRecord
    from app.models.warehouse import Warehouse


class ForecastResult(Base):
    __tablename__ = "forecast_results"
    __table_args__ = (
        CheckConstraint("horizon_days IN (7, 30)", name="ck_forecast_results_horizon"),
        CheckConstraint(
            "forecast_end_date = forecast_start_date + (horizon_days - 1)",
            name="ck_forecast_results_date_range",
        ),
        CheckConstraint(
            "predicted_demand >= 0 AND current_stock >= 0 AND recommended_replenishment >= 0",
            name="ck_forecast_results_quantities",
        ),
        CheckConstraint(
            f"data_type IN ({enum_sql_values(DataType)})",
            name="ck_forecast_results_data_type",
        ),
        UniqueConstraint("task_id", name="uq_forecast_results_task"),
        Index(
            "ix_forecast_results_scope_generated",
            "cooperative_id",
            "warehouse_id",
            "product_id",
            text("generated_at DESC"),
        ),
    )

    created_at = None  # type: ignore[assignment]  # generated_at is the only timestamp
    updated_at = None  # type: ignore[assignment]

    cooperative_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    model_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("model_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    task_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("task_records.id", ondelete="SET NULL")
    )
    horizon_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    forecast_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    forecast_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_demand: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    current_stock: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    recommended_replenishment: Mapped[float] = mapped_column(
        Numeric(14, 3), nullable=False
    )
    data_type: Mapped[DataType] = mapped_column(
        SqlEnum(
            DataType,
            native_enum=False,
            create_constraint=False,
            name="ck_forecast_results_data_type",
            length=16,
        ),
        nullable=False,
    )
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    important_factors: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    limitation_notice: Mapped[str] = mapped_column(String(500), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    cooperative: Mapped[Cooperative] = relationship("Cooperative")
    warehouse: Mapped[Warehouse] = relationship("Warehouse")
    product: Mapped[Product] = relationship("Product")
    model_version: Mapped[ModelVersion] = relationship(
        "ModelVersion", back_populates="forecast_results"
    )
    task: Mapped[TaskRecord | None] = relationship("TaskRecord")
    points: Mapped[list[ForecastPoint]] = relationship(
        "ForecastPoint",
        back_populates="forecast_result",
        cascade="all, delete-orphan",
        order_by="ForecastPoint.forecast_date",
    )


__all__ = ["ForecastResult"]
