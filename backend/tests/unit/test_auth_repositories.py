from __future__ import annotations

import pytest
import pytest_asyncio
from app.models import Cooperative, Permission, Role, User, UserWarehouse, Warehouse
from app.models.base import Base
from app.repositories.auth import (
    CooperativeRepository,
    PermissionRepository,
    RoleRepository,
    UserRepository,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def auth_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    uuid_defaults = []
    for table in Base.metadata.tables.values():
        id_column = table.c.get("id")
        if id_column is not None and id_column.server_default is not None:
            uuid_defaults.append((id_column, id_column.server_default))
            id_column.server_default = None

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    for column, server_default in uuid_defaults:
        column.server_default = server_default

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_repository_loads_role_permissions_cooperative_and_warehouses(
    auth_session: AsyncSession,
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
    auth_session.add(user)
    await auth_session.commit()

    loaded = await UserRepository(auth_session).get_by_username_with_access(
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
    auth_session: AsyncSession,
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
    auth_session.add(user)
    await auth_session.commit()

    warehouses = await UserRepository(auth_session).list_authorized_warehouses(
        user.id
    )

    assert [warehouse.code for warehouse in warehouses] == ["same"]


@pytest.mark.asyncio
async def test_cooperative_repository_gets_by_code(auth_session: AsyncSession) -> None:
    auth_session.add(Cooperative(code="coop-unique", name="合作社"))
    await auth_session.commit()

    loaded = await CooperativeRepository(auth_session).get_by_code("coop-unique")

    assert loaded is not None
    assert loaded.name == "合作社"


@pytest.mark.asyncio
async def test_role_and_permission_repositories_load_by_code(
    auth_session: AsyncSession,
) -> None:
    permission = Permission(
        code="batch:read", name="批次查询", module="batch"
    )
    auth_session.add(Role(code="COOPERATIVE_ADMIN", name="合作社管理员", permissions=[permission]))
    await auth_session.commit()

    role = await RoleRepository(auth_session).get_by_code_with_permissions(
        "COOPERATIVE_ADMIN"
    )
    loaded_permission = await PermissionRepository(auth_session).get_by_code("batch:read")

    assert role is not None
    assert [item.code for item in role.permissions] == ["batch:read"]
    assert loaded_permission is not None
    assert loaded_permission.module == "batch"
