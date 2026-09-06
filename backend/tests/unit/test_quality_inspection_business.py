from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.models import (
    InspectionConclusion,
    QualityInspection,
    TraceEvent,
    TraceEventType,
)
from app.schemas.quality_inspection import QualityInspectionCreate
from app.services.quality_inspection import QualityInspectionService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import batch_factory, role_factory, user_factory


def _context(user, *, role_code: str = "COOPERATIVE_ADMIN", permissions=None):
    return AuthContext(
        user_id=user.id,
        username=user.username,
        real_name=user.real_name,
        role_code=role_code,
        permission_codes=frozenset(permissions or {"batch:manage"}),
        cooperative_id=user.cooperative_id,
        warehouse_ids=None,
        session_id="session",
        token_id="token",
    )


def _payload(
    *,
    conclusion: InspectionConclusion = InspectionConclusion.PASSED,
    original_inspection_id=None,
    result: str = "13.2",
    is_qualified: bool = True,
) -> QualityInspectionCreate:
    return QualityInspectionCreate(
        inspection_date=date(2026, 9, 5),
        conclusion=conclusion,
        original_inspection_id=original_inspection_id,
        items=[
            {
                "name": "水分含量",
                "value": result,
                "unit": "%",
                "standard": "≤14.0%",
                "isQualified": is_qualified,
            }
        ],
    )


@pytest.mark.asyncio
async def test_quality_service_creates_and_lists_inspection(
    postgres_session: AsyncSession,
) -> None:
    user = user_factory(role=role_factory(code="COOPERATIVE_ADMIN"))
    batch = batch_factory(cooperative=user.cooperative, creator=user)
    postgres_session.add(batch)
    await postgres_session.commit()
    context = _context(user)

    service = QualityInspectionService(postgres_session)
    created = await service.create(context, batch.id, _payload())
    assert created.conclusion is InspectionConclusion.PASSED
    assert created.inspector_id == user.id
    assert created.inspection_no.startswith("QC-")

    event = await postgres_session.scalar(
        select(TraceEvent).where(TraceEvent.batch_id == batch.id)
    )
    assert event is not None
    assert event.event_type is TraceEventType.INSPECTION
    assert event.source_type == "QUALITY_INSPECTION"
    assert event.public_data["conclusion"] == "PASSED"
    assert "remarks" not in event.public_data
    await postgres_session.commit()

    listed, total = await service.list(context, batch.id)
    assert total == 1
    assert listed[0].id == created.id
    assert listed[0].items[0].item_name == "水分含量"


@pytest.mark.asyncio
async def test_quality_service_keeps_correction_as_a_new_record(
    postgres_session: AsyncSession,
) -> None:
    user = user_factory(role=role_factory(code="COOPERATIVE_ADMIN"))
    batch = batch_factory(cooperative=user.cooperative, creator=user)
    postgres_session.add(batch)
    await postgres_session.commit()
    context = _context(user)
    service = QualityInspectionService(postgres_session)

    original = await service.create(
        context,
        batch.id,
        _payload(conclusion=InspectionConclusion.FAILED, result="18.0", is_qualified=False),
    )
    correction = await service.create(
        context,
        batch.id,
        _payload(original_inspection_id=original.id),
    )

    assert correction.id != original.id
    assert correction.original_inspection_id == original.id
    assert await postgres_session.scalar(
        select(QualityInspection.id).where(QualityInspection.id == original.id)
    ) == original.id


@pytest.mark.asyncio
async def test_quality_service_rejects_correction_from_another_batch(
    postgres_session: AsyncSession,
) -> None:
    user = user_factory(role=role_factory(code="COOPERATIVE_ADMIN"))
    first_batch = batch_factory(cooperative=user.cooperative, creator=user)
    second_batch = batch_factory(cooperative=user.cooperative, creator=user)
    postgres_session.add_all([first_batch, second_batch])
    await postgres_session.commit()
    context = _context(user)
    service = QualityInspectionService(postgres_session)
    original = await service.create(context, first_batch.id, _payload())

    with pytest.raises(AppException) as error:
        await service.create(
            context,
            second_batch.id,
            _payload(original_inspection_id=original.id),
        )
    assert error.value.code == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_quality_service_rejects_warehouse_staff_without_authorized_warehouse(
    postgres_session: AsyncSession,
) -> None:
    user = user_factory(role=role_factory(code="WAREHOUSE_STAFF"))
    batch = batch_factory(cooperative=user.cooperative, creator=user)
    postgres_session.add(batch)
    await postgres_session.commit()
    context = _context(user, role_code="WAREHOUSE_STAFF")
    context = replace(context, warehouse_ids=frozenset())

    with pytest.raises(AppException) as error:
        await QualityInspectionService(postgres_session).create(
            context, batch.id, _payload()
        )
    assert error.value.code == "RESOURCE_NOT_FOUND"
