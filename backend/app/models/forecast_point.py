from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.forecast_result import ForecastResult


class ForecastPoint(Base):
    __tablename__ = "forecast_points"
    __table_args__ = (
        CheckConstraint(
            "predicted_quantity >= 0 AND lower_bound >= 0 AND upper_bound >= 0",
            name="ck_forecast_points_nonnegative",
        ),
        CheckConstraint(
            "lower_bound <= predicted_quantity AND predicted_quantity <= upper_bound",
            name="ck_forecast_points_bounds",
        ),
        UniqueConstraint(
            "forecast_result_id", "forecast_date", name="uq_forecast_points_result_date"
        ),
    )

    created_at = None
    updated_at = None

    forecast_result_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("forecast_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    lower_bound: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    upper_bound: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)

    forecast_result: Mapped[ForecastResult] = relationship(
        "ForecastResult", back_populates="points"
    )


__all__ = ["ForecastPoint"]
