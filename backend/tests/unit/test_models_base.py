from pathlib import Path

from app.models import AuditLog, Cooperative, UserWarehouse
from app.models import Base as ExportedBase
from app.models.base import Base
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


def test_base_is_the_single_declarative_base_with_common_columns() -> None:
    assert issubclass(Base, DeclarativeBase)
    assert {
        "cooperatives",
        "roles",
        "permissions",
        "role_permissions",
        "users",
        "warehouses",
        "user_warehouses",
    }.issubset(Base.metadata.tables)
    assert {"id", "created_at", "updated_at"}.issubset(Base.__dict__)


def test_models_inherit_the_common_base_columns() -> None:
    assert {"id", "created_at", "updated_at"}.issubset(
        {column.name for column in inspect(Cooperative).columns}
    )
    assert {"id", "created_at", "updated_at"}.issubset(
        {column.name for column in inspect(AuditLog).columns}
    )
    assert "id" not in {column.name for column in inspect(UserWarehouse).columns}
    assert "updated_at" not in {
        column.name for column in inspect(UserWarehouse).columns
    }


def test_models_package_exports_the_same_base_class() -> None:
    assert ExportedBase is Base


def test_alembic_uses_the_shared_orm_metadata() -> None:
    alembic_env = Path(__file__).resolve().parents[2] / "alembic" / "env.py"
    source = alembic_env.read_text(encoding="utf-8")

    assert "from app.models import Base" in source
    assert "target_metadata = Base.metadata" in source
