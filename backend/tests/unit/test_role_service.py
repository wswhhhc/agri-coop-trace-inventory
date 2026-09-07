from __future__ import annotations

from uuid import uuid4

import pytest
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.models import Permission, Role
from app.schemas.role import RolePermissionsUpdate
from app.services.role import RoleService


def _context(role_code: str = "SYSTEM_ADMIN") -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="role-test",
        real_name="角色测试",
        role_code=role_code,
        permission_codes=frozenset(),
        cooperative_id=None,
        warehouse_ids=None,
        session_id="session",
        token_id="token",
    )


async def _seed_role(postgres_session, *, with_second_permission: bool = False):
    read = Permission(
        code="inventory:read",
        name="库存查看",
        module="inventory",
        description="查看库存",
    )
    write = Permission(
        code="inventory:write",
        name="库存维护",
        module="inventory",
        description="维护库存",
    )
    role = Role(
        code=f"ROLE_{uuid4().hex[:8].upper()}",
        name="测试角色",
        permissions=[read, write] if with_second_permission else [read],
    )
    postgres_session.add(role)
    await postgres_session.commit()
    return role, read, write


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_role_service_lists_roles_and_permissions(postgres_session) -> None:
    role, read, _ = await _seed_role(postgres_session)

    service = RoleService(postgres_session)
    roles = await service.list_roles(_context())
    permissions = await service.list_permissions(_context())

    assert [item.code for item in roles] == [role.code]
    assert [item.code for item in roles[0].permissions] == [read.code]
    assert [item.code for item in permissions] == [read.code]


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_role_service_replaces_permissions_by_code(postgres_session) -> None:
    role, _, write = await _seed_role(postgres_session, with_second_permission=True)

    updated = await RoleService(postgres_session).update_permissions(
        _context(), role.id, RolePermissionsUpdate(permission_codes=[write.code])
    )

    assert [permission.code for permission in updated.permissions] == [write.code]


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_role_service_rejects_duplicate_permission_codes(postgres_session) -> None:
    with pytest.raises(AppException) as error:
        await RoleService(postgres_session).update_permissions(
            _context(),
            uuid4(),
            RolePermissionsUpdate(
                permission_codes=["inventory:read", "inventory:read"]
            ),
        )

    assert (error.value.status_code, error.value.code) == (400, "BAD_REQUEST")


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_role_service_returns_not_found_for_unknown_role_or_permission(
    postgres_session,
) -> None:
    role, _, _ = await _seed_role(postgres_session)
    service = RoleService(postgres_session)

    with pytest.raises(AppException) as permission_error:
        await service.update_permissions(
            _context(), role.id, RolePermissionsUpdate(permission_codes=["unknown:read"])
        )
    with pytest.raises(AppException) as role_error:
        await service.update_permissions(
            _context(), uuid4(), RolePermissionsUpdate(permission_codes=[])
        )

    assert (permission_error.value.status_code, permission_error.value.code) == (
        404,
        "RESOURCE_NOT_FOUND",
    )
    assert (role_error.value.status_code, role_error.value.code) == (
        404,
        "RESOURCE_NOT_FOUND",
    )


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_role_service_requires_system_admin(postgres_session) -> None:
    await _seed_role(postgres_session)

    with pytest.raises(AppException) as error:
        await RoleService(postgres_session).list_roles(_context("COOPERATIVE_ADMIN"))

    assert (error.value.status_code, error.value.code) == (403, "PERMISSION_DENIED")
