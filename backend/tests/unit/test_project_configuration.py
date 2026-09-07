import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_project_does_not_depend_on_the_conflicting_myapplication_package() -> None:
    project = tomllib.loads(
        (PROJECT_ROOT.parent / "pyproject.toml").read_text(encoding="utf-8")
    )
    lockfile = tomllib.loads(
        (PROJECT_ROOT.parent / "uv.lock").read_text(encoding="utf-8")
    )

    dependencies = project["project"]["dependencies"]
    locked_packages = {package["name"] for package in lockfile["package"]}

    assert not any(dependency.startswith("myapplication") for dependency in dependencies)
    assert "myapplication" not in locked_packages
    assert "flask" not in locked_packages


def test_alembic_resolves_the_backend_app_package_from_any_working_directory() -> None:
    alembic_config = (PROJECT_ROOT / "alembic.ini").read_text(encoding="utf-8")

    assert "prepend_sys_path = %(here)s" in alembic_config
