from pathlib import Path

from app.models import Base as ExportedBase
from app.models.base import Base
from sqlalchemy.orm import DeclarativeBase


def test_base_is_a_declarative_base_without_predefined_table_attributes() -> None:
    assert issubclass(Base, DeclarativeBase)
    assert Base.metadata.tables == {}
    assert not any(
        attribute_name in Base.__dict__
        for attribute_name in ("id", "created_at", "updated_at", "cooperative_id")
    )


def test_models_package_exports_the_same_base_class() -> None:
    assert ExportedBase is Base


def test_alembic_uses_the_shared_orm_metadata() -> None:
    alembic_env = Path(__file__).resolve().parents[2] / "alembic" / "env.py"
    source = alembic_env.read_text(encoding="utf-8")

    assert "from app.models import Base" in source
    assert "target_metadata = Base.metadata" in source
