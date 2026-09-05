import re
from pathlib import Path

import pytest
from pwdlib import PasswordHash

from scripts.generate_demo_data import (
    DEMO_PASSWORD_HASH,
    generate_demo_sql,
    get_demo_password,
    permission_codes_by_role,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _row_counts(sql: str) -> dict[str, int]:
    return {
        table: int(count)
        for table, count in re.findall(
            r"^-- ROW_COUNT ([a-z_]+): (\d+)$", sql, re.MULTILINE
        )
    }


def test_same_seed_generates_identical_sql() -> None:
    assert generate_demo_sql(20260904) == generate_demo_sql(20260904)


def test_different_seed_changes_generated_sql() -> None:
    assert generate_demo_sql(20260904) != generate_demo_sql(20260905)


def test_demo_data_has_expected_scale_and_synthetic_markers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEMO_PASSWORD", "Demo@123456")
    sql = generate_demo_sql(20260904)
    counts = _row_counts(sql)

    assert counts["cooperatives"] == 2
    assert counts["warehouses"] == 4
    assert counts["users"] == 7
    assert counts["products"] == 8
    assert counts["batches"] == 24
    assert counts["quality_inspections"] == 24
    assert counts["inventory_transactions"] >= 1400
    assert counts["alerts"] >= 12
    assert counts["model_versions"] == 16
    assert counts["forecast_points"] == 112
    assert "SYNTHETIC" in sql
    assert "全部为虚构合成数据" in sql
    assert get_demo_password() not in sql
    assert "$argon2" in sql


def test_insert_order_follows_foreign_key_dependencies() -> None:
    sql = generate_demo_sql(20260904)
    ordered_tables = [
        "cooperatives",
        "roles",
        "users",
        "warehouses",
        "products",
        "batches",
        "inventory_operations",
        "inventory_transactions",
        "task_records",
        "model_versions",
        "forecast_results",
        "forecast_points",
        "audit_logs",
    ]
    positions = [sql.index(f"INSERT INTO {table}") for table in ordered_tables]

    assert positions == sorted(positions)
    assert sql.count("ON CONFLICT DO NOTHING;") >= len(ordered_tables)


def test_checked_in_demo_sql_is_current() -> None:
    committed_sql = (PROJECT_ROOT / "sql" / "demo_data.sql").read_text(encoding="utf-8")

    assert committed_sql == generate_demo_sql(20260904)


def test_demo_password_from_environment_matches_stored_argon2_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEMO_PASSWORD", "Demo@123456")

    assert PasswordHash.recommended().verify(get_demo_password(), DEMO_PASSWORD_HASH)


def test_role_permissions_follow_documented_boundaries() -> None:
    permissions = permission_codes_by_role()

    assert permissions["SYSTEM_ADMIN"] == [
        "cooperative:manage",
        "user:manage",
        "inventory:read",
        "trace:read",
        "alert:read",
        "model:read",
        "audit:read",
    ]
    assert "model:manage" not in permissions["SYSTEM_ADMIN"]
    assert "model:read" in permissions["COOPERATIVE_ADMIN"]
    assert "model:read" in permissions["WAREHOUSE_STAFF"]
    assert "alert:handle" in permissions["WAREHOUSE_STAFF"]
    assert "audit:read" in permissions["WAREHOUSE_STAFF"]


def test_demo_models_use_xgboost_with_moving_average_as_baseline() -> None:
    sql = generate_demo_sql(20260904)

    assert "RANDOM_FOREST" not in sql
    assert "XGBOOST" in sql
