from __future__ import annotations

import pytest
from app.models import Cooperative, Permission, Role, User, UserWarehouse, Warehouse
from app.repositories.auth import (
    CooperativeRepository,
    PermissionRepository,
    RoleRepository,
    UserRepository,
    WarehouseRepository,
)
from sqlalchemy.ext.asyncio import AsyncSession


def test_each_repository_lives_in_its_own_module() -> None:
    assert CooperativeRepository.__module__ == "app.repositories.cooperative"
    assert UserRepository.__module__ == "app.repositories.user"
    assert RoleRepository.__module__ == "app.repositories.role"
    assert PermissionRepository.__module__ == "app.repositories.permission"
    assert WarehouseRepository.__module__ == "app.repositories.warehouse"


@pytest.mark.asyncio
async def test_user_repository_loads_role_permissions_cooperative_and_warehouses(
    postgres_session: AsyncSession,
) -> None:
    cooperative = Cooperative(code="coop-1", name="第一合作社")
    role = Role(code="WAREHOUSE_STAFF", name="仓库工作人员")
    role.permissions.append(
        Permission(code="inventory:read", name="库存查询", module="inventory")
    )
    user = User(
        cooperative=cooperative,
        role=role,
        username="warehouse_staff",
        password_hash="hashed",
        real_name="仓库人员",
    )
    warehouse = Warehouse(
        cooperative=cooperative,
        code="main",
        name="中心仓",
    )
    user.user_warehouses.append(UserWarehouse(warehouse=warehouse))
    postgres_session.add(user)
    await postgres_session.commit()

    loaded = await UserRepository(postgres_session).get_by_username_with_access(
        "warehouse_staff"
    )

    assert loaded is not None
    assert loaded.cooperative is not None
    assert loaded.cooperative.code == "coop-1"
    assert loaded.role.code == "WAREHOUSE_STAFF"
    assert [permission.code for permission in loaded.role.permissions] == [
        "inventory:read"
    ]
    assert [item.warehouse.code for item in loaded.user_warehouses] == ["main"]


@pytest.mark.asyncio
async def test_warehouse_repository_returns_only_same_cooperative_authorizations(
    postgres_session: AsyncSession,
) -> None:
    first_cooperative = Cooperative(code="coop-1", name="第一合作社")
    second_cooperative = Cooperative(code="coop-2", name="第二合作社")
    role = Role(code="WAREHOUSE_STAFF", name="仓库工作人员")
    user = User(
        cooperative=first_cooperative,
        role=role,
        username="staff_scope",
        password_hash="hashed",
        real_name="仓库人员",
    )
    same_cooperative_warehouse = Warehouse(
        cooperative=first_cooperative,
        code="same",
        name="同合作社仓库",
    )
    other_cooperative_warehouse = Warehouse(
        cooperative=second_cooperative,
        code="other",
        name="其他合作社仓库",
    )
    user.user_warehouses.extend(
        [
            UserWarehouse(warehouse=same_cooperative_warehouse),
            UserWarehouse(warehouse=other_cooperative_warehouse),
        ]
    )
    postgres_session.add(user)
    await postgres_session.commit()

    warehouses = await UserRepository(postgres_session).list_authorized_warehouses(
        user.id
    )

    assert [warehouse.code for warehouse in warehouses] == ["same"]


@pytest.mark.asyncio
async def test_cooperative_repository_gets_by_code(postgres_session: AsyncSession) -> None:
    postgres_session.add(Cooperative(code="coop-unique", name="合作社"))
    await postgres_session.commit()

    loaded = await CooperativeRepository(postgres_session).get_by_code("coop-unique")

    assert loaded is not None
    assert loaded.name == "合作社"


@pytest.mark.asyncio
async def test_role_and_permission_repositories_load_by_code(
    postgres_session: AsyncSession,
) -> None:
    permission = Permission(
        code="batch:read", name="批次查询", module="batch"
    )
    postgres_session.add(Role(code="COOPERATIVE_ADMIN", name="合作社管理员", permissions=[permission]))
    await postgres_session.commit()

    role = await RoleRepository(postgres_session).get_by_code_with_permissions(
        "COOPERATIVE_ADMIN"
    )
    loaded_permission = await PermissionRepository(postgres_session).get_by_code("batch:read")

    assert role is not None
    assert [item.code for item in role.permissions] == ["batch:read"]
    assert loaded_permission is not None
    assert loaded_permission.module == "batch"
