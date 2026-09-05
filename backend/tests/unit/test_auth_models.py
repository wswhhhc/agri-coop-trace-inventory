from __future__ import annotations

from uuid import uuid4

import pytest
from app.models import (
    Cooperative,
    Permission,
    Role,
    User,
    UserWarehouse,
    Warehouse,
)
from app.models.base import Base
from sqlalchemy import inspect


def test_auth_models_register_database_tables_and_relationships() -> None:
    expected_tables = {
        "cooperatives",
        "roles",
        "permissions",
        "role_permissions",
        "users",
        "warehouses",
        "user_warehouses",
    }

    assert expected_tables.issubset(Base.metadata.tables)
    assert {column.name for column in User.__table__.columns} == {
        "id",
        "cooperative_id",
        "role_id",
        "username",
        "password_hash",
        "real_name",
        "phone",
        "status",
        "last_login_at",
        "created_at",
        "updated_at",
    }
    assert inspect(User).relationships["role"].mapper.class_ is Role
    assert inspect(User).relationships["cooperative"].mapper.class_ is Cooperative
    assert inspect(User).relationships["user_warehouses"].mapper.class_ is UserWarehouse
    assert inspect(Role).relationships["permissions"].mapper.class_ is Permission
    assert inspect(Warehouse).relationships["user_warehouses"].mapper.class_ is UserWarehouse


def test_each_auth_model_lives_in_its_own_module() -> None:
    assert Cooperative.__module__ == "app.models.cooperative"
    assert User.__module__ == "app.models.user"
    assert Role.__module__ == "app.models.role"
    assert Permission.__module__ == "app.models.permission"
    assert Warehouse.__module__ == "app.models.warehouse"
    assert UserWarehouse.__module__ == "app.models.user_warehouse"


def test_system_admin_can_be_created_without_cooperative() -> None:
    system_admin = User(
        id=uuid4(),
        role=Role(code="SYSTEM_ADMIN", name="系统管理员"),
        username="sysadmin",
        password_hash="hashed",
        real_name="平台管理员",
    )

    system_admin.validate_cooperative_scope()


def test_non_system_user_must_belong_to_a_cooperative() -> None:
    user = User(
        id=uuid4(),
        role=Role(code="COOPERATIVE_ADMIN", name="合作社管理员"),
        username="coop_admin",
        password_hash="hashed",
        real_name="合作社管理员",
    )

    with pytest.raises(ValueError, match="非系统管理员用户必须关联合作社"):
        user.validate_cooperative_scope()
