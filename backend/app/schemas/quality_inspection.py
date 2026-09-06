from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import (
    AliasChoices,
    AwareDatetime,
    Field,
    field_validator,
    model_validator,
)

from app.models.enums import InspectionConclusion
from app.schemas.common import BaseSchema, PageParams


class QualityInspectionItemCreate(BaseSchema):
    item_name: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("name", "itemName", "item_name"),
        serialization_alias="name",
    )
    result_value: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("value", "resultValue", "result_value"),
        serialization_alias="value",
    )
    unit: str | None = Field(default=None, max_length=20)
    standard_value: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("standard", "standardValue", "standard_value"),
        serialization_alias="standard",
    )
    is_qualified: bool = Field(
        validation_alias=AliasChoices("isQualified", "is_qualified")
    )

    @field_validator("item_name", "result_value", "standard_value")
    @classmethod
    def trim_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("文本不能为空")
        return value


class QualityInspectionCreate(BaseSchema):
    inspection_date: date = Field(
        validation_alias=AliasChoices("inspectionDate", "inspection_date")
    )
    conclusion: InspectionConclusion = InspectionConclusion.PENDING
    items: list[QualityInspectionItemCreate] = Field(min_length=1, max_length=100)
    attachment_file_ids: list[UUID] = Field(
        default_factory=list,
        validation_alias=AliasChoices("attachmentFileIds", "attachment_file_ids"),
        max_length=20,
    )
    original_inspection_id: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("originalInspectionId", "original_inspection_id"),
    )
    remarks: str | None = Field(
        default=None,
        max_length=500,
        validation_alias=AliasChoices("remark", "remarks"),
        serialization_alias="remark",
    )

    @model_validator(mode="after")
    def validate_items_and_conclusion(self) -> QualityInspectionCreate:
        names = [item.item_name for item in self.items]
        if len(names) != len(set(names)):
            raise ValueError("同一次质检的项目名称不能重复")
        if self.conclusion is InspectionConclusion.PASSED and any(
            not item.is_qualified for item in self.items
        ):
            raise ValueError("存在不合格项目时不能提交 PASSED 结论")
        return self

    @field_validator("attachment_file_ids")
    @classmethod
    def validate_attachment_ids(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("附件不能重复关联")
        return value


class QualityInspectionListParams(PageParams):
    conclusion: InspectionConclusion | None = None


class QualityInspectionItemData(BaseSchema):
    id: UUID
    name: str
    value: str
    unit: str | None
    standard: str
    is_qualified: bool
    sort_order: int


class QualityInspectionData(BaseSchema):
    id: UUID
    cooperative_id: UUID
    batch_id: UUID
    inspection_no: str
    inspection_date: date
    inspector_id: UUID
    inspector_name: str
    conclusion: InspectionConclusion
    remarks: str | None
    original_inspection_id: UUID | None
    items: list[QualityInspectionItemData]
    attachment_file_ids: list[UUID]
    created_at: AwareDatetime
    updated_at: AwareDatetime


__all__ = [
    "QualityInspectionCreate",
    "QualityInspectionData",
    "QualityInspectionItemCreate",
    "QualityInspectionItemData",
    "QualityInspectionListParams",
]
