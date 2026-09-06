from __future__ import annotations

from uuid import UUID

from pydantic import AwareDatetime, Field

from app.schemas.common import BaseSchema


class FileData(BaseSchema):
    id: UUID
    original_name: str
    content_type: str = Field(serialization_alias="contentType")
    size: int
    download_url: str = Field(serialization_alias="downloadUrl")
    created_at: AwareDatetime


__all__ = ["FileData"]
