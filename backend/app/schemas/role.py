from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema


class PermissionData(BaseSchema):
    id: UUID
    code: str
    name: str
    module: str
    description: str | None


class RoleData(BaseSchema):
    id: UUID
    code: str
    name: str
    description: str | None
    is_system: bool
    permissions: list[PermissionData]


class RolePermissionsUpdate(BaseSchema):
    permission_codes: list[str] = Field(default_factory=list, max_length=200)


__all__ = ["PermissionData", "RoleData", "RolePermissionsUpdate"]
