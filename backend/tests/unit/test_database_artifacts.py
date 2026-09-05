import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TABLES = {
    "cooperatives",
    "roles",
    "permissions",
    "role_permissions",
    "users",
    "warehouses",
    "user_warehouses",
    "product_categories",
    "products",
    "batches",
    "quality_inspections",
    "quality_inspection_items",
    "files",
    "inspection_files",
    "inventories",
    "inventory_operations",
    "inventory_transactions",
    "trace_events",
    "alert_rules",
    "alerts",
    "alert_handling_logs",
    "task_records",
    "idempotency_records",
    "model_versions",
    "forecast_results",
    "forecast_points",
    "audit_logs",
}


def _migration_source() -> str:
    revisions = list((PROJECT_ROOT / "alembic" / "versions").glob("e4f3c0ebc976_*.py"))
    assert len(revisions) == 1, "必须保留唯一的初始迁移版本"
    return revisions[0].read_text(encoding="utf-8")


def _permission_migration_source() -> str:
    revisions = list((PROJECT_ROOT / "alembic" / "versions").glob("a1b2c3d4e5f6_*.py"))
    assert len(revisions) == 1, "必须提供唯一的权限修正迁移版本"
    return revisions[0].read_text(encoding="utf-8")


def _least_privilege_migration_source() -> str:
    revisions = list((PROJECT_ROOT / "alembic" / "versions").glob("b2c3d4e5f6a7_*.py"))
    assert len(revisions) == 1, "必须提供唯一的最小权限迁移版本"
    return revisions[0].read_text(encoding="utf-8")


def _xgboost_migration_source() -> str:
    revisions = list((PROJECT_ROOT / "alembic" / "versions").glob("c3d4e5f6a7b8_*.py"))
    assert len(revisions) == 1, "必须提供唯一的 XGBoost 演示数据迁移版本"
    return revisions[0].read_text(encoding="utf-8")


def _audit_permission_migration_source() -> str:
    revisions = list((PROJECT_ROOT / "alembic" / "versions").glob("d4e5f6a7b8c9_*.py"))
    assert len(revisions) == 1, "必须提供唯一的审计查看权限迁移版本"
    return revisions[0].read_text(encoding="utf-8")


def _idempotency_path_migration_source() -> str:
    revisions = list((PROJECT_ROOT / "alembic" / "versions").glob("e5f6a7b8c9d0_*.py"))
    assert len(revisions) == 1, "必须提供唯一的幂等接口路径迁移版本"
    return revisions[0].read_text(encoding="utf-8")


def test_initial_migration_creates_and_drops_every_table() -> None:
    source = _migration_source()
    created = set(re.findall(r'op\.create_table\(\s*["\']([^"\']+)', source))
    dropped = set(re.findall(r'op\.drop_table\(\s*["\']([^"\']+)', source))

    assert created == EXPECTED_TABLES
    assert dropped == EXPECTED_TABLES


def test_initial_migration_contains_database_guards() -> None:
    source = _migration_source()

    assert "pgcrypto" in source
    assert "uq_alerts_active_dedupe" in source
    assert "uq_model_versions_active_scope" in source
    assert "prevent_immutable_record_mutation" in source


def test_permission_migration_repairs_legacy_demo_data() -> None:
    source = _permission_migration_source()

    assert "SYSTEM_ADMIN" in source
    assert "WAREHOUSE_STAFF" in source
    assert "inventory:write" in source
    assert "alert:handle" in source
    assert "ON CONFLICT (role_id, permission_id) DO NOTHING" in source


def test_least_privilege_migration_adds_model_read_permission() -> None:
    source = _least_privilege_migration_source()

    assert "model:read" in source
    assert "SYSTEM_ADMIN" in source
    assert "WAREHOUSE_STAFF" in source
    assert "model:manage" in source


def test_xgboost_migration_normalizes_legacy_demo_models() -> None:
    source = _xgboost_migration_source()

    assert "model_type = 'XGBOOST'" in source
    assert "RANDOM_FOREST" in source
    assert "SYNTHETIC" in source


def test_audit_permission_migration_limits_staff_to_own_logs() -> None:
    source = _audit_permission_migration_source()

    assert "audit:read" in source
    assert "WAREHOUSE_STAFF" in source


def test_idempotency_path_migration_matches_interface_contract() -> None:
    source = _idempotency_path_migration_source()

    assert "/api/v1/inventory-outbounds" in source
    assert "/api/v1/inventory-issues" in source


def test_schema_sql_matches_initial_migration_tables() -> None:
    schema_path = PROJECT_ROOT / "sql" / "schema.sql"
    assert schema_path.exists(), "必须提供供评审和部署使用的 schema.sql"

    schema = schema_path.read_text(encoding="utf-8")
    created = set(re.findall(r"CREATE TABLE ([a-z_]+)", schema))
    created.discard("alembic_version")

    assert created == EXPECTED_TABLES
    assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in schema
