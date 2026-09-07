from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import httpx
import pytest
from app.api.roles import get_role_service
from app.core.auth.context import AuthContext
from app.core.auth.dependencies import get_auth_context
from app.main import create_app

ROLE_ID = UUID("11111111-1111-1111-1111-111111111111")
PERMISSION_ID = UUID("22222222-2222-2222-2222-222222222222")


def _permission(*, code: str = "inventory:read") -> SimpleNamespace:
    return SimpleNamespace(
        id=PERMISSION_ID,
        code=code,
        name="库存查看",
        module="inventory",
        description="查看库存",
    )


def _role() -> SimpleNamespace:
    return SimpleNamespace(
        id=ROLE_ID,
        code="SYSTEM_ADMIN",
        name="系统管理员",
        description="系统级管理角色",
        is_system=True,
        permissions=[_permission()],
    )


def _context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="system-admin",
        real_name="系统管理员",
        role_code="SYSTEM_ADMIN",
        permission_codes=frozenset(),
        cooperative_id=None,
        warehouse_ids=None,
        session_id="session",
        token_id="token",
    )


class FakeRoleService:
    def __init__(self) -> None:
        self.updated_role_id: UUID | None = None
        self.updated_permission_codes: list[str] | None = None

    async def list_roles(self, context: AuthContext) -> list[SimpleNamespace]:
        return [_role()]

    async def list_permissions(self, context: AuthContext) -> list[SimpleNamespace]:
        return [_permission()]

    async def update_permissions(self, context, role_id, payload):
        self.updated_role_id = role_id
        self.updated_permission_codes = payload.permission_codes
        return _role()


def _application(service: FakeRoleService):
    application = create_app()
    application.dependency_overrides[get_auth_context] = _context
    application.dependency_overrides[get_role_service] = lambda: service
    return application


def test_roles_openapi_uses_nested_permission_route_and_permission_codes() -> None:
    paths = create_app().openapi()["paths"]

    assert "/api/v1/roles" in paths
    assert "/api/v1/roles/permissions" in paths
    assert "/api/v1/roles/{roleId}/permissions" in paths
    assert "/api/v1/permissions" not in paths

    request_schema = paths["/api/v1/roles/{roleId}/permissions"]["put"][
        "requestBody"
    ]["content"]["application/json"]["schema"]
    schema_name = request_schema["$ref"].rsplit("/", maxsplit=1)[-1]
    properties = create_app().openapi()["components"]["schemas"][schema_name][
        "properties"
    ]
    assert "permissionCodes" in properties
    assert "permissionIds" not in properties


@pytest.mark.asyncio
async def test_role_permission_endpoints_return_contract_data_and_forward_codes() -> None:
    service = FakeRoleService()
    transport = httpx.ASGITransport(app=_application(service))

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        roles = await client.get("/api/v1/roles")
        permissions = await client.get("/api/v1/roles/permissions")
        updated = await client.put(
            f"/api/v1/roles/{ROLE_ID}/permissions",
            json={"permissionCodes": ["inventory:read", "batch:manage"]},
        )

    assert roles.status_code == 200
    assert roles.json()["data"][0]["permissions"][0]["code"] == "inventory:read"
    assert roles.json()["pagination"]["totalItems"] == 1
    assert permissions.status_code == 200
    assert permissions.json()["data"][0]["code"] == "inventory:read"
    assert updated.status_code == 200
    assert service.updated_role_id == ROLE_ID
    assert service.updated_permission_codes == ["inventory:read", "batch:manage"]


@pytest.mark.asyncio
async def test_role_permission_endpoint_rejects_legacy_route_and_field() -> None:
    service = FakeRoleService()
    transport = httpx.ASGITransport(app=_application(service))

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        legacy_route = await client.get("/api/v1/permissions")
        legacy_field = await client.put(
            f"/api/v1/roles/{ROLE_ID}/permissions",
            json={"permissionIds": [str(PERMISSION_ID)]},
        )

    assert legacy_route.status_code == 404
    assert legacy_field.status_code == 422
    assert legacy_field.json()["error"]["code"] == "VALIDATION_ERROR"


def test_interface_document_matches_runtime_role_permission_contract() -> None:
    project_root = Path(__file__).resolve().parents[3]
    document = (project_root / "docs" / "接口设计说明书.md").read_text(encoding="utf-8")

    assert "| GET | `/roles/permissions` |" in document
    assert "| GET | `/permissions` |" not in document
    assert "permissionCodes" in document
    assert "permissionIds" not in document
