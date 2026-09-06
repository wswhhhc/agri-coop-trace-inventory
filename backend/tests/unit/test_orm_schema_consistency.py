import re
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.models import Base
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ORM_TABLE_COLUMNS = {
    "cooperatives": {
        "id",
        "code",
        "name",
        "contact_name",
        "contact_phone",
        "address",
        "status",
        "created_at",
        "updated_at",
    },
    "roles": {
        "id",
        "code",
        "name",
        "description",
        "is_system",
        "created_at",
        "updated_at",
    },
    "permissions": {
        "id",
        "code",
        "name",
        "module",
        "description",
        "created_at",
        "updated_at",
    },
    "role_permissions": {"role_id", "permission_id"},
    "users": {
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
    },
    "warehouses": {
        "id",
        "cooperative_id",
        "code",
        "name",
        "address",
        "manager_name",
        "status",
        "created_at",
        "updated_at",
    },
    "user_warehouses": {"user_id", "warehouse_id", "created_at"},
    "product_categories": {
        "id",
        "cooperative_id",
        "code",
        "name",
        "description",
        "is_active",
        "created_at",
        "updated_at",
    },
    "products": {
        "id",
        "cooperative_id",
        "category_id",
        "code",
        "name",
        "unit",
        "shelf_life_days",
        "safety_stock",
        "is_active",
        "created_at",
        "updated_at",
    },
    "batches": {
        "id",
        "cooperative_id",
        "product_id",
        "batch_no",
        "trace_code",
        "origin",
        "production_date",
        "expiry_date",
        "responsible_person",
        "status",
        "created_by",
        "created_at",
        "updated_at",
    },
    "files": {
        "id",
        "cooperative_id",
        "original_name",
        "storage_key",
        "mime_type",
        "size_bytes",
        "sha256",
        "uploaded_by",
        "created_at",
    },
    "quality_inspections": {
        "id",
        "cooperative_id",
        "batch_id",
        "inspection_no",
        "inspected_at",
        "inspector_id",
        "conclusion",
        "remarks",
        "original_inspection_id",
        "created_at",
        "updated_at",
    },
    "quality_inspection_items": {
        "id",
        "inspection_id",
        "item_name",
        "unit",
        "standard_value",
        "result_value",
        "is_qualified",
        "sort_order",
        "created_at",
    },
    "inspection_files": {"inspection_id", "file_id", "created_at"},
    "inventories": {
        "id",
        "cooperative_id",
        "warehouse_id",
        "batch_id",
        "quantity",
        "locked_quantity",
        "version",
        "updated_at",
    },
    "inventory_operations": {
        "id",
        "cooperative_id",
        "operation_no",
        "operation_type",
        "source_warehouse_id",
        "destination_warehouse_id",
        "external_reference",
        "reason",
        "occurred_at",
        "status",
        "created_by",
        "created_at",
    },
    "inventory_transactions": {
        "id",
        "cooperative_id",
        "operation_id",
        "warehouse_id",
        "batch_id",
        "transaction_type",
        "quantity_delta",
        "quantity_before",
        "quantity_after",
        "occurred_at",
        "created_by",
        "created_at",
    },
    "idempotency_records": {
        "id",
        "cooperative_id",
        "user_id",
        "endpoint",
        "idempotency_key",
        "request_hash",
        "status",
        "response_status",
        "response_body",
        "expires_at",
        "created_at",
        "updated_at",
    },
    "trace_events": {
        "id",
        "cooperative_id",
        "batch_id",
        "event_type",
        "title",
        "description",
        "event_time",
        "source_type",
        "source_id",
        "public_data",
        "created_by",
        "created_at",
    },
    "alert_rules": {
        "id", "cooperative_id", "warehouse_id", "product_id", "alert_type",
        "threshold_quantity", "threshold_days", "turnover_days", "severity",
        "is_enabled", "created_at", "updated_at",
    },
    "alerts": {
        "id", "cooperative_id", "rule_id", "alert_type", "severity", "status",
        "warehouse_id", "product_id", "batch_id", "dedupe_key", "title", "message",
        "evidence", "detected_at", "resolved_at", "assignee_id", "created_at", "updated_at",
    },
    "alert_handling_logs": {
        "id", "alert_id", "operator_id", "from_status", "to_status", "comment", "created_at",
    },
    "task_records": {
        "id", "cooperative_id", "task_type", "celery_task_id", "status", "progress",
        "request_payload", "result_payload", "error_code", "error_message", "requested_by",
        "started_at", "finished_at", "created_at", "updated_at",
    },
}


def _schema_columns(table_name: str) -> set[str]:
    schema = (PROJECT_ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    match = re.search(
        rf"CREATE TABLE {table_name} \((.*?)\n\);", schema, flags=re.DOTALL
    )
    assert match is not None, f"schema.sql 缺少表 {table_name}"
    return set(
        re.findall(r"^    ([a-z_][a-z0-9_]*)\s+", match.group(1), flags=re.MULTILINE)
    )


def test_orm_columns_match_schema_sql_for_the_current_orm_scope() -> None:
    for table_name, expected_columns in ORM_TABLE_COLUMNS.items():
        assert table_name in Base.metadata.tables
        orm_columns = set(Base.metadata.tables[table_name].columns.keys())
        assert orm_columns == expected_columns
        assert _schema_columns(table_name) == expected_columns


def test_target_tables_have_foreign_keys_and_expected_indexes() -> None:
    assert {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables["products"].foreign_keys
    } == {"cooperatives.id", "product_categories.id"}
    assert {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables["batches"].foreign_keys
    } == {"cooperatives.id", "products.id", "users.id"}
    assert {index.name for index in Base.metadata.tables["products"].indexes} == {
        "ix_products_cooperative_active_name"
    }
    assert {index.name for index in Base.metadata.tables["batches"].indexes} == {
        "ix_batches_cooperative_product_production",
        "ix_batches_cooperative_expiry",
    }
    assert {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables["quality_inspections"].foreign_keys
    } == {
        "cooperatives.id",
        "batches.id",
        "users.id",
        "quality_inspections.id",
    }
    assert {
        index.name for index in Base.metadata.tables["quality_inspections"].indexes
    } == {
        "ix_quality_inspections_batch_time",
        "ix_quality_inspections_original",
    }
    assert {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables["inventories"].foreign_keys
    } == {"cooperatives.id", "warehouses.id", "batches.id"}
    assert {
        index.name for index in Base.metadata.tables["inventories"].indexes
    } == {"ix_inventories_cooperative_warehouse"}
    assert {
        index.name
        for index in Base.metadata.tables["inventory_operations"].indexes
    } == {"uq_inventory_operations_external_reference"}
    assert {
        index.name
        for index in Base.metadata.tables["inventory_transactions"].indexes
    } == {
        "ix_inventory_transactions_warehouse_time",
        "ix_inventory_transactions_batch_time",
    }
    assert {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables["trace_events"].foreign_keys
    } == {"cooperatives.id", "batches.id", "users.id"}
    assert {
        index.name for index in Base.metadata.tables["trace_events"].indexes
    } == {"ix_trace_events_batch_time"}
    assert {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables["alert_rules"].foreign_keys
    } == {"cooperatives.id", "warehouses.id", "products.id"}
    assert {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables["alerts"].foreign_keys
    } == {
        "cooperatives.id", "alert_rules.id", "warehouses.id", "products.id",
        "batches.id", "users.id",
    }
    assert {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables["alert_handling_logs"].foreign_keys
    } == {"alerts.id", "users.id"}
    assert {
        index.name for index in Base.metadata.tables["alert_rules"].indexes
    } == {"ix_alert_rules_scope"}
    assert {
        index.name for index in Base.metadata.tables["alerts"].indexes
    } == {"uq_alerts_active_dedupe", "ix_alerts_workbench"}
    assert {
        index.name for index in Base.metadata.tables["alert_handling_logs"].indexes
    } == {"ix_alert_handling_logs_alert_time"}
    assert {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables["task_records"].foreign_keys
    } == {"cooperatives.id", "users.id"}
    assert {
        index.name for index in Base.metadata.tables["task_records"].indexes
    } == {"ix_task_records_cooperative_created"}
    assert {
        constraint.name for constraint in Base.metadata.tables["task_records"].constraints
    } >= {"uq_task_records_celery_id"}


@pytest.mark.asyncio
async def test_alembic_check_has_no_differences_for_the_shared_metadata(
    postgres_engine: AsyncEngine,
    postgres_database_url: str,
) -> None:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", postgres_database_url)

    async with postgres_engine.begin() as connection:
        await connection.execute(
            text(
                "CREATE TABLE alembic_version "
                "(version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
            )
        )
        await connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES ('f6a7b8c9d0e1')")
        )
        await connection.run_sync(
            lambda sync_connection: command.check(
                _config_with_connection(config, sync_connection)
            )
        )


def _config_with_connection(config: Config, connection: object) -> Config:
    config.attributes["connection"] = connection
    return config
