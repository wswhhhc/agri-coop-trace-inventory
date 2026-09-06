from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from app.models import (
    Base,
    Batch,
    Cooperative,
    File,
    InspectionConclusion,
    InspectionFile,
    QualityInspection,
    QualityInspectionItem,
    Role,
    User,
)
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import product_factory


def test_quality_models_are_registered_and_split_by_business() -> None:
    assert QualityInspection.__module__ == "app.models.quality_inspection"
    assert QualityInspectionItem.__module__ == "app.models.quality_inspection_item"
    assert File.__module__ == "app.models.file"
    assert InspectionFile.__module__ == "app.models.inspection_file"
    assert {
        "quality_inspections",
        "quality_inspection_items",
        "files",
        "inspection_files",
    }.issubset(Base.metadata.tables)
    assert (
        inspect(QualityInspection).relationships["batch"].mapper.class_ is Batch
    )
    assert (
        inspect(QualityInspection).relationships["inspector"].mapper.class_ is User
    )
    assert (
        inspect(QualityInspectionItem).relationships["inspection"].mapper.class_
        is QualityInspection
    )
    assert inspect(File).relationships["inspection_links"].mapper.class_ is InspectionFile


def test_quality_models_have_contract_columns_and_constraints() -> None:
    assert {
        "id",
        "cooperative_id",
        "batch_id",
        "inspection_no",
        "inspected_at",
        "inspector_id",
        "conclusion",
        "remarks",
        "original_inspection_id",
        "created_at",
        "updated_at",
    } == {column.name for column in inspect(QualityInspection).columns}
    assert {
        "id",
        "inspection_id",
        "item_name",
        "unit",
        "standard_value",
        "result_value",
        "is_qualified",
        "sort_order",
        "created_at",
    } == {column.name for column in inspect(QualityInspectionItem).columns}
    assert inspect(QualityInspection).columns.conclusion.type.enum_class is InspectionConclusion
    assert {constraint.name for constraint in QualityInspection.__table__.constraints} >= {
        "ck_quality_inspections_conclusion",
        "uq_quality_inspections_cooperative_no",
    }
    assert {constraint.name for constraint in QualityInspectionItem.__table__.constraints} >= {
        "ck_inspection_items_sort_order",
        "uq_inspection_items_name",
    }


@pytest.mark.asyncio
async def test_quality_models_can_be_created_and_queried(
    postgres_session: AsyncSession,
) -> None:
    cooperative = Cooperative(code="quality-coop", name="质检合作社")
    role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
    user = User(
        cooperative=cooperative,
        role=role,
        username="quality_admin",
        password_hash="hashed",
        real_name="质检管理员",
    )
    product = product_factory(cooperative=cooperative)
    batch = Batch(
        cooperative=cooperative,
        product=product,
        batch_no="quality-batch",
        trace_code="quality-trace",
        origin="测试基地",
        production_date=date(2026, 9, 5),
        expiry_date=date(2026, 9, 12),
        creator=user,
    )
    inspection = QualityInspection(
        cooperative=cooperative,
        batch=batch,
        inspector=user,
        inspection_no="QC-001",
        inspected_at=datetime(2026, 9, 5, 8, 0, tzinfo=UTC),
        conclusion=InspectionConclusion.PASSED,
    )
    inspection.items.append(
        QualityInspectionItem(
            item_name="水分",
            unit="%",
            standard_value="≤14",
            result_value="13.2",
            is_qualified=True,
        )
    )
    postgres_session.add(inspection)
    await postgres_session.commit()

    loaded = await postgres_session.scalar(
        select(QualityInspection).where(QualityInspection.inspection_no == "QC-001")
    )
    assert loaded is not None
    assert loaded.items[0].unit == "%"
