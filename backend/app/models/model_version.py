from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DataType, ModelType, enum_sql_values

if TYPE_CHECKING:
    from app.models.cooperative import Cooperative
    from app.models.forecast_result import ForecastResult
    from app.models.product import Product
    from app.models.task_record import TaskRecord
    from app.models.user import User
    from app.models.warehouse import Warehouse


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        CheckConstraint(
            f"model_type IN ({enum_sql_values(ModelType)})",
            name="ck_model_versions_type",
        ),
        CheckConstraint(
            f"data_type IN ({enum_sql_values(DataType)})",
            name="ck_model_versions_data_type",
        ),
        CheckConstraint(
            "training_end_date >= training_start_date",
            name="ck_model_versions_training_dates",
        ),
        UniqueConstraint(
            "cooperative_id", "version", name="uq_model_versions_cooperative_version"
        ),
        UniqueConstraint("task_id", name="uq_model_versions_task"),
        Index(
            "uq_model_versions_active_scope",
            "cooperative_id",
            "warehouse_id",
            "product_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    updated_at = None  # type: ignore[assignment]  # model_versions only records creation time

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
    task_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("task_records.id", ondelete="SET NULL")
    )
    model_type: Mapped[ModelType] = mapped_column(
        SqlEnum(
            ModelType,
            native_enum=False,
            create_constraint=False,
            name="ck_model_versions_type",
            length=24,
        ),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(String(255))
    data_type: Mapped[DataType] = mapped_column(
        SqlEnum(
            DataType,
            native_enum=False,
            create_constraint=False,
            name="ck_model_versions_data_type",
            length=16,
        ),
        nullable=False,
    )
    training_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    training_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    random_seed: Mapped[int] = mapped_column(nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    cooperative: Mapped[Cooperative] = relationship("Cooperative")
    warehouse: Mapped[Warehouse] = relationship("Warehouse")
    product: Mapped[Product] = relationship("Product")
    task: Mapped[TaskRecord | None] = relationship("TaskRecord")
    creator: Mapped[User] = relationship("User")
    forecast_results: Mapped[list[ForecastResult]] = relationship(
        "ForecastResult", back_populates="model_version"
    )


__all__ = ["ModelVersion"]
