from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

import pytest
from app.core.auth.authorization import (
    ensure_cooperative_scope,
    ensure_warehouse_scope,
    permission_denied,
    require_cooperative_scope,
    require_permission,
    require_warehouse_scope,
    resource_not_found,
)
from app.core.auth.context import AuthContext
from app.core.auth.dependencies import get_auth_context
from app.core.exceptions import AppException, app_exception_handler
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

COOPERATIVE_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_COOPERATIVE_ID = UUID("22222222-2222-2222-2222-222222222222")
WAREHOUSE_ID = UUID("33333333-3333-3333-3333-333333333333")
OTHER_WAREHOUSE_ID = UUID("44444444-4444-4444-4444-444444444444")


def _context(
    *,
    cooperative_id: UUID | None = COOPERATIVE_ID,
    warehouse_ids: frozenset[UUID] | None = frozenset({WAREHOUSE_ID}),
    permissions: frozenset[str] = frozenset({"inventory:read"}),
) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="tester",
        real_name="测试用户",
        role_code="WAREHOUSE_STAFF",
        permission_codes=permissions,
        cooperative_id=cooperative_id,
        warehouse_ids=warehouse_ids,
        session_id="session-1",
        token_id="token-1",
    )


def test_auth_context_checks_cooperative_scope() -> None:
    context = _context()
    global_context = _context(cooperative_id=None, warehouse_ids=None)

    assert context.has_cooperative_access(COOPERATIVE_ID) is True
    assert context.has_cooperative_access(OTHER_COOPERATIVE_ID) is False
    assert global_context.has_cooperative_access(OTHER_COOPERATIVE_ID) is True


def test_scope_helpers_reject_ids_outside_auth_context_scope() -> None:
    context = _context()

    ensure_cooperative_scope(context, COOPERATIVE_ID)
    ensure_warehouse_scope(context, WAREHOUSE_ID)

    with pytest.raises(AppException) as cooperative_error:
        ensure_cooperative_scope(context, OTHER_COOPERATIVE_ID)
    with pytest.raises(AppException) as warehouse_error:
        ensure_warehouse_scope(context, OTHER_WAREHOUSE_ID)

    assert cooperative_error.value.status_code == 403
    assert cooperative_error.value.code == "SCOPE_ACCESS_DENIED"
    assert warehouse_error.value.status_code == 403
    assert warehouse_error.value.code == "SCOPE_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_permission_dependency_returns_context_when_permission_exists() -> None:
    context = _context(permissions=frozenset({"inventory:write"}))

    result = await require_permission("inventory:write")(context)

    assert result is context


@pytest.mark.asyncio
async def test_permission_dependency_returns_403_when_permission_is_missing() -> None:
    with pytest.raises(AppException) as error:
        await require_permission("inventory:write")(_context())

    assert error.value.status_code == 403
    assert error.value.code == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_cooperative_scope_dependency_returns_context_for_matching_scope() -> None:
    context = _context()

    result = await require_cooperative_scope(COOPERATIVE_ID, context)

    assert result is context


@pytest.mark.asyncio
async def test_cooperative_scope_dependency_returns_403_for_other_scope() -> None:
    with pytest.raises(AppException) as error:
        await require_cooperative_scope(OTHER_COOPERATIVE_ID, _context())

    assert error.value.status_code == 403
    assert error.value.code == "SCOPE_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_global_context_can_pass_cooperative_and_warehouse_scope() -> None:
    context = _context(cooperative_id=None, warehouse_ids=None)

    assert await require_cooperative_scope(OTHER_COOPERATIVE_ID, context) is context
    assert await require_warehouse_scope(OTHER_WAREHOUSE_ID, context) is context


@pytest.mark.asyncio
async def test_warehouse_scope_dependency_returns_403_for_unauthorized_warehouse() -> None:
    with pytest.raises(AppException) as error:
        await require_warehouse_scope(OTHER_WAREHOUSE_ID, _context())

    assert error.value.status_code == 403
    assert error.value.code == "SCOPE_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_empty_warehouse_scope_cannot_access_any_warehouse() -> None:
    with pytest.raises(AppException) as error:
        await require_warehouse_scope(WAREHOUSE_ID, _context(warehouse_ids=frozenset()))

    assert error.value.status_code == 403
    assert error.value.code == "SCOPE_ACCESS_DENIED"


def test_fastapi_dependencies_bind_camel_case_path_parameter_and_error_status() -> None:
    application = FastAPI()
    context = _context(permissions=frozenset({"inventory:write"}))

    async def override_auth_context() -> AuthContext:
        return context

    application.dependency_overrides[get_auth_context] = override_auth_context
    application.add_exception_handler(AppException, app_exception_handler)

    @application.get("/cooperatives/{cooperativeId}")
    async def cooperative_endpoint(
        _: Annotated[AuthContext, Depends(require_cooperative_scope)],
    ) -> dict[str, bool]:
        return {"ok": True}

    @application.post(
        "/inventory",
        dependencies=[Depends(require_permission("inventory:write"))],
    )
    async def inventory_endpoint() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(application)

    assert client.get(f"/cooperatives/{COOPERATIVE_ID}").status_code == 200
    denied = client.get(f"/cooperatives/{OTHER_COOPERATIVE_ID}")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "SCOPE_ACCESS_DENIED"
    assert client.post("/inventory").status_code == 200

    async def override_without_write_permission() -> AuthContext:
        return _context()

    application.dependency_overrides[get_auth_context] = override_without_write_permission
    permission_denied_response = client.post("/inventory")
    assert permission_denied_response.status_code == 403
    assert permission_denied_response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_authorization_errors_use_public_error_contract() -> None:
    denied = permission_denied()
    missing = resource_not_found()

    assert (denied.status_code, denied.code) == (403, "PERMISSION_DENIED")
    assert (missing.status_code, missing.code) == (404, "RESOURCE_NOT_FOUND")
