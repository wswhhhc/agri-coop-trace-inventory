from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from app.models import InspectionConclusion
from app.schemas.quality_inspection import QualityInspectionCreate
from pydantic import ValidationError


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "inspectionDate": "2026-09-05",
        "conclusion": "PASSED",
        "items": [
            {
                "name": "水分含量",
                "value": "13.2",
                "unit": "%",
                "standard": "≤14.0%",
                "isQualified": True,
            }
        ],
        "attachmentFileIds": [],
    }
    payload.update(overrides)
    return payload


def test_quality_create_accepts_public_contract_aliases() -> None:
    payload = QualityInspectionCreate(**_payload())

    assert payload.inspection_date == date(2026, 9, 5)
    assert payload.conclusion is InspectionConclusion.PASSED
    assert payload.items[0].item_name == "水分含量"
    assert payload.items[0].standard_value == "≤14.0%"
    assert payload.items[0].unit == "%"


def test_quality_create_rejects_passed_when_item_is_unqualified() -> None:
    with pytest.raises(ValidationError, match="PASSED"):
        QualityInspectionCreate(
            **_payload(
                items=[
                    {
                        "name": "农残",
                        "value": "超标",
                        "standard": "不得检出",
                        "isQualified": False,
                    }
                ]
            )
        )


def test_quality_create_requires_at_least_one_item_and_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        QualityInspectionCreate(**_payload(items=[]))
    with pytest.raises(ValidationError):
        QualityInspectionCreate(**_payload(unexpected="bad"))


def test_quality_create_accepts_correction_reference() -> None:
    original_id = uuid4()
    payload = QualityInspectionCreate(
        **_payload(originalInspectionId=str(original_id), conclusion="PENDING")
    )

    assert payload.original_inspection_id == original_id


def test_quality_create_rejects_duplicate_attachments() -> None:
    file_id = uuid4()
    with pytest.raises(ValidationError, match="附件不能重复"):
        QualityInspectionCreate(
            **_payload(attachmentFileIds=[str(file_id), str(file_id)])
        )
