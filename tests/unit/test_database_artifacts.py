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
    revisions = list((PROJECT_ROOT / "alembic" / "versions").glob("*.py"))
    assert len(revisions) == 1, "初始阶段必须且只能有一个迁移版本"
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


def test_schema_sql_matches_initial_migration_tables() -> None:
    schema_path = PROJECT_ROOT / "sql" / "schema.sql"
    assert schema_path.exists(), "必须提供供评审和部署使用的 schema.sql"

    schema = schema_path.read_text(encoding="utf-8")
    created = set(re.findall(r"CREATE TABLE ([a-z_]+)", schema))
    created.discard("alembic_version")

    assert created == EXPECTED_TABLES
    assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in schema
