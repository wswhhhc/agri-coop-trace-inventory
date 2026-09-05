"""初始化数据库结构

Revision ID: e4f3c0ebc976
Revises:
Create Date: 2026-09-04 13:27:00.856305
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e4f3c0ebc976"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def _id_column() -> sa.Column:
    return sa.Column(
        "id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )


def _created_at_column() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def _updated_at_column() -> sa.Column:
    return sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def upgrade() -> None:
    """创建V1数据库结构。"""
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "cooperatives",
        _id_column(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("contact_name", sa.String(50)),
        sa.Column("contact_phone", sa.String(20)),
        sa.Column("address", sa.String(255)),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_cooperatives_status"
        ),
        sa.UniqueConstraint("code", name="uq_cooperatives_code"),
    )
    op.create_table(
        "roles",
        _id_column(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        _created_at_column(),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )
    op.create_table(
        "permissions",
        _id_column(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("module", sa.String(32), nullable=False),
        sa.Column("description", sa.String(255)),
        _created_at_column(),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            UUID,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            UUID,
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "users",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "role_id",
            UUID,
            sa.ForeignKey("roles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("real_name", sa.String(50), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint(
            "username = lower(username)", name="ck_users_username_lower"
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'LOCKED', 'INACTIVE')", name="ck_users_status"
        ),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index(
        "ix_users_cooperative_status", "users", ["cooperative_id", "status"]
    )
    op.create_table(
        "warehouses",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("address", sa.String(255)),
        sa.Column("manager_name", sa.String(50)),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_warehouses_status"
        ),
        sa.UniqueConstraint(
            "cooperative_id", "code", name="uq_warehouses_cooperative_code"
        ),
    )
    op.create_index(
        "ix_warehouses_cooperative_status",
        "warehouses",
        ["cooperative_id", "status"],
    )
    op.create_table(
        "user_warehouses",
        sa.Column(
            "user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "warehouse_id",
            UUID,
            sa.ForeignKey("warehouses.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _created_at_column(),
    )

    op.create_table(
        "product_categories",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _created_at_column(),
        _updated_at_column(),
        sa.UniqueConstraint(
            "cooperative_id", "code", name="uq_product_categories_cooperative_code"
        ),
        sa.UniqueConstraint(
            "cooperative_id", "name", name="uq_product_categories_cooperative_name"
        ),
    )
    op.create_table(
        "products",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            UUID,
            sa.ForeignKey("product_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("shelf_life_days", sa.Integer(), nullable=False),
        sa.Column(
            "safety_stock", sa.Numeric(14, 3), nullable=False, server_default="0"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint("shelf_life_days > 0", name="ck_products_shelf_life"),
        sa.CheckConstraint("safety_stock >= 0", name="ck_products_safety_stock"),
        sa.UniqueConstraint(
            "cooperative_id", "code", name="uq_products_cooperative_code"
        ),
    )
    op.create_index(
        "ix_products_cooperative_active_name",
        "products",
        ["cooperative_id", "is_active", "name"],
    )
    op.create_table(
        "batches",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            UUID,
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("batch_no", sa.String(64), nullable=False),
        sa.Column("trace_code", sa.String(64), nullable=False),
        sa.Column("origin", sa.String(255), nullable=False),
        sa.Column("production_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("responsible_person", sa.String(50)),
        sa.Column("status", sa.String(20), nullable=False, server_default="CREATED"),
        sa.Column(
            "created_by",
            UUID,
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint(
            "expiry_date >= production_date", name="ck_batches_date_order"
        ),
        sa.CheckConstraint(
            "status IN ('CREATED', 'IN_STOCK', 'DEPLETED', 'BLOCKED', 'EXPIRED')",
            name="ck_batches_status",
        ),
        sa.UniqueConstraint("batch_no", name="uq_batches_batch_no"),
        sa.UniqueConstraint("trace_code", name="uq_batches_trace_code"),
    )
    op.create_index(
        "ix_batches_cooperative_product_production",
        "batches",
        ["cooperative_id", "product_id", sa.text("production_date DESC")],
    )
    op.create_index(
        "ix_batches_cooperative_expiry", "batches", ["cooperative_id", "expiry_date"]
    )
    op.create_table(
        "files",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column(
            "uploaded_by",
            UUID,
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        _created_at_column(),
        sa.CheckConstraint("size_bytes > 0", name="ck_files_size_positive"),
        sa.UniqueConstraint("storage_key", name="uq_files_storage_key"),
    )
    op.create_table(
        "quality_inspections",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "batch_id",
            UUID,
            sa.ForeignKey("batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("inspection_no", sa.String(64), nullable=False),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "inspector_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "conclusion", sa.String(16), nullable=False, server_default="PENDING"
        ),
        sa.Column("remarks", sa.String(500)),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint(
            "conclusion IN ('PENDING', 'PASSED', 'FAILED')",
            name="ck_quality_inspections_conclusion",
        ),
        sa.UniqueConstraint(
            "cooperative_id",
            "inspection_no",
            name="uq_quality_inspections_cooperative_no",
        ),
    )
    op.create_index(
        "ix_quality_inspections_batch_time",
        "quality_inspections",
        ["batch_id", sa.text("inspected_at DESC")],
    )
    op.create_table(
        "quality_inspection_items",
        _id_column(),
        sa.Column(
            "inspection_id",
            UUID,
            sa.ForeignKey("quality_inspections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_name", sa.String(100), nullable=False),
        sa.Column("standard_value", sa.String(100), nullable=False),
        sa.Column("result_value", sa.String(100), nullable=False),
        sa.Column("is_qualified", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        _created_at_column(),
        sa.CheckConstraint("sort_order >= 0", name="ck_inspection_items_sort_order"),
        sa.UniqueConstraint(
            "inspection_id", "item_name", name="uq_inspection_items_name"
        ),
    )
    op.create_table(
        "inspection_files",
        sa.Column(
            "inspection_id",
            UUID,
            sa.ForeignKey("quality_inspections.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "file_id",
            UUID,
            sa.ForeignKey("files.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _created_at_column(),
    )

    op.create_table(
        "inventories",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id",
            UUID,
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "batch_id",
            UUID,
            sa.ForeignKey("batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column(
            "locked_quantity", sa.Numeric(14, 3), nullable=False, server_default="0"
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        _updated_at_column(),
        sa.CheckConstraint("quantity >= 0", name="ck_inventories_quantity"),
        sa.CheckConstraint(
            "locked_quantity >= 0 AND locked_quantity <= quantity",
            name="ck_inventories_locked_quantity",
        ),
        sa.CheckConstraint("version >= 0", name="ck_inventories_version"),
        sa.UniqueConstraint(
            "warehouse_id", "batch_id", name="uq_inventories_warehouse_batch"
        ),
    )
    op.create_index(
        "ix_inventories_cooperative_warehouse",
        "inventories",
        ["cooperative_id", "warehouse_id"],
    )
    op.create_table(
        "inventory_operations",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("operation_no", sa.String(64), nullable=False),
        sa.Column("operation_type", sa.String(24), nullable=False),
        sa.Column(
            "source_warehouse_id",
            UUID,
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "destination_warehouse_id",
            UUID,
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
        ),
        sa.Column("external_reference", sa.String(100)),
        sa.Column("reason", sa.String(500)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="COMPLETED"),
        sa.Column(
            "created_by",
            UUID,
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        _created_at_column(),
        sa.CheckConstraint(
            "operation_type IN "
            "('INBOUND', 'OUTBOUND', 'ADJUSTMENT', 'DAMAGE', 'TRANSFER')",
            name="ck_inventory_operations_type",
        ),
        sa.CheckConstraint(
            "status IN ('COMPLETED', 'REVERSED')", name="ck_inventory_operations_status"
        ),
        sa.CheckConstraint(
            "(operation_type = 'TRANSFER' "
            "AND source_warehouse_id IS NOT NULL "
            "AND destination_warehouse_id IS NOT NULL "
            "AND source_warehouse_id <> destination_warehouse_id) "
            "OR (operation_type <> 'TRANSFER' "
            "AND source_warehouse_id IS NULL "
            "AND destination_warehouse_id IS NULL)",
            name="ck_inventory_operations_transfer_warehouses",
        ),
        sa.UniqueConstraint("operation_no", name="uq_inventory_operations_no"),
    )
    op.create_index(
        "uq_inventory_operations_external_reference",
        "inventory_operations",
        ["cooperative_id", "external_reference"],
        unique=True,
        postgresql_where=sa.text("external_reference IS NOT NULL"),
    )
    op.create_table(
        "inventory_transactions",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "operation_id",
            UUID,
            sa.ForeignKey("inventory_operations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id",
            UUID,
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "batch_id",
            UUID,
            sa.ForeignKey("batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("transaction_type", sa.String(24), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(14, 3), nullable=False),
        sa.Column("quantity_before", sa.Numeric(14, 3), nullable=False),
        sa.Column("quantity_after", sa.Numeric(14, 3), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_by",
            UUID,
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        _created_at_column(),
        sa.CheckConstraint(
            "transaction_type IN "
            "('INBOUND', 'OUTBOUND', 'ADJUSTMENT', 'DAMAGE', "
            "'TRANSFER_OUT', 'TRANSFER_IN')",
            name="ck_inventory_transactions_type",
        ),
        sa.CheckConstraint(
            "quantity_before >= 0 AND quantity_after >= 0",
            name="ck_inventory_transactions_nonnegative",
        ),
        sa.CheckConstraint(
            "quantity_delta <> 0", name="ck_inventory_transactions_delta_nonzero"
        ),
        sa.CheckConstraint(
            "quantity_before + quantity_delta = quantity_after",
            name="ck_inventory_transactions_balance",
        ),
        sa.CheckConstraint(
            "(transaction_type IN ('INBOUND', 'TRANSFER_IN') AND quantity_delta > 0) "
            "OR (transaction_type IN ('OUTBOUND', 'DAMAGE', 'TRANSFER_OUT') "
            "AND quantity_delta < 0) OR transaction_type = 'ADJUSTMENT'",
            name="ck_inventory_transactions_delta_direction",
        ),
    )
    op.create_index(
        "ix_inventory_transactions_warehouse_time",
        "inventory_transactions",
        ["cooperative_id", "warehouse_id", sa.text("occurred_at DESC")],
    )
    op.create_index(
        "ix_inventory_transactions_batch_time",
        "inventory_transactions",
        ["batch_id", "occurred_at"],
    )
    op.create_table(
        "trace_events",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "batch_id",
            UUID,
            sa.ForeignKey("batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500)),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(32)),
        sa.Column("source_id", UUID),
        sa.Column(
            "public_data", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        _created_at_column(),
        sa.CheckConstraint(
            "event_type IN ('PRODUCTION', 'INSPECTION', 'INBOUND', 'OUTBOUND', "
            "'TRANSFER', 'OTHER')",
            name="ck_trace_events_type",
        ),
    )
    op.create_index(
        "ix_trace_events_batch_time", "trace_events", ["batch_id", "event_time", "id"]
    )

    op.create_table(
        "alert_rules",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id", UUID, sa.ForeignKey("warehouses.id", ondelete="RESTRICT")
        ),
        sa.Column(
            "product_id", UUID, sa.ForeignKey("products.id", ondelete="RESTRICT")
        ),
        sa.Column("alert_type", sa.String(24), nullable=False),
        sa.Column("threshold_quantity", sa.Numeric(14, 3)),
        sa.Column("threshold_days", sa.Integer()),
        sa.Column("turnover_days", sa.Integer()),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint(
            "alert_type IN ('LOW_STOCK', 'NEAR_EXPIRY', 'OVERSTOCK', 'QUALITY_FAILED')",
            name="ck_alert_rules_type",
        ),
        sa.CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_alert_rules_severity",
        ),
        sa.CheckConstraint(
            "threshold_quantity IS NULL OR threshold_quantity >= 0",
            name="ck_alert_rules_threshold_quantity",
        ),
        sa.CheckConstraint(
            "threshold_days IS NULL OR threshold_days >= 0",
            name="ck_alert_rules_threshold_days",
        ),
        sa.CheckConstraint(
            "turnover_days IS NULL OR turnover_days >= 0",
            name="ck_alert_rules_turnover_days",
        ),
    )
    op.create_index(
        "ix_alert_rules_scope",
        "alert_rules",
        ["cooperative_id", "warehouse_id", "product_id", "alert_type"],
    )
    op.create_table(
        "alerts",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rule_id", UUID, sa.ForeignKey("alert_rules.id", ondelete="SET NULL")
        ),
        sa.Column("alert_type", sa.String(24), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column(
            "warehouse_id", UUID, sa.ForeignKey("warehouses.id", ondelete="RESTRICT")
        ),
        sa.Column(
            "product_id", UUID, sa.ForeignKey("products.id", ondelete="RESTRICT")
        ),
        sa.Column("batch_id", UUID, sa.ForeignKey("batches.id", ondelete="RESTRICT")),
        sa.Column("dedupe_key", sa.String(160), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column(
            "evidence", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("assignee_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint(
            "alert_type IN ('LOW_STOCK', 'NEAR_EXPIRY', 'OVERSTOCK', 'QUALITY_FAILED')",
            name="ck_alerts_type",
        ),
        sa.CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_alerts_severity",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'RESOLVED', 'IGNORED')",
            name="ck_alerts_status",
        ),
        sa.CheckConstraint(
            "(status IN ('PENDING', 'PROCESSING') AND resolved_at IS NULL) "
            "OR (status IN ('RESOLVED', 'IGNORED') AND resolved_at IS NOT NULL)",
            name="ck_alerts_resolution_time",
        ),
    )
    op.create_index(
        "uq_alerts_active_dedupe",
        "alerts",
        ["cooperative_id", "dedupe_key"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'PROCESSING')"),
    )
    op.create_index(
        "ix_alerts_workbench",
        "alerts",
        ["cooperative_id", "status", "severity", sa.text("detected_at DESC")],
    )
    op.create_table(
        "alert_handling_logs",
        _id_column(),
        sa.Column(
            "alert_id",
            UUID,
            sa.ForeignKey("alerts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "operator_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(16), nullable=False),
        sa.Column("to_status", sa.String(16), nullable=False),
        sa.Column("comment", sa.String(500)),
        _created_at_column(),
        sa.CheckConstraint(
            "from_status IN ('PENDING', 'PROCESSING', 'RESOLVED', 'IGNORED')",
            name="ck_alert_handling_logs_from_status",
        ),
        sa.CheckConstraint(
            "to_status IN ('PENDING', 'PROCESSING', 'RESOLVED', 'IGNORED')",
            name="ck_alert_handling_logs_to_status",
        ),
    )
    op.create_index(
        "ix_alert_handling_logs_alert_time",
        "alert_handling_logs",
        ["alert_id", "created_at"],
    )
    op.create_table(
        "task_records",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        ),
        sa.Column("task_type", sa.String(32), nullable=False),
        sa.Column("celery_task_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("progress", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column(
            "request_payload",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("result_payload", JSONB),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.String(500)),
        sa.Column("requested_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILURE', 'RETRY')",
            name="ck_task_records_status",
        ),
        sa.CheckConstraint(
            "progress BETWEEN 0 AND 100", name="ck_task_records_progress"
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR started_at IS NOT NULL",
            name="ck_task_records_time_order_presence",
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_task_records_time_order",
        ),
        sa.UniqueConstraint("celery_task_id", name="uq_task_records_celery_id"),
    )
    op.create_index(
        "ix_task_records_cooperative_created",
        "task_records",
        ["cooperative_id", sa.text("created_at DESC")],
    )
    op.create_table(
        "idempotency_records",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.String(160), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PROCESSING"),
        sa.Column("response_status", sa.SmallInteger()),
        sa.Column("response_body", JSONB),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        _created_at_column(),
        _updated_at_column(),
        sa.CheckConstraint(
            "status IN ('PROCESSING', 'COMPLETED', 'FAILED')",
            name="ck_idempotency_records_status",
        ),
        sa.CheckConstraint(
            "response_status IS NULL OR response_status BETWEEN 100 AND 599",
            name="ck_idempotency_records_response_status",
        ),
        sa.CheckConstraint(
            "expires_at > created_at", name="ck_idempotency_records_expiry"
        ),
        sa.UniqueConstraint(
            "user_id",
            "endpoint",
            "idempotency_key",
            name="uq_idempotency_records_request",
        ),
    )
    op.create_index(
        "ix_idempotency_records_expiry", "idempotency_records", ["expires_at"]
    )

    op.create_table(
        "model_versions",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id",
            UUID,
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            UUID,
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "task_id", UUID, sa.ForeignKey("task_records.id", ondelete="SET NULL")
        ),
        sa.Column("model_type", sa.String(24), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("artifact_path", sa.String(255)),
        sa.Column("data_type", sa.String(16), nullable=False),
        sa.Column("training_start_date", sa.Date(), nullable=False),
        sa.Column("training_end_date", sa.Date(), nullable=False),
        sa.Column("random_seed", sa.Integer(), nullable=False),
        sa.Column(
            "parameters", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "metrics", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_by",
            UUID,
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        _created_at_column(),
        sa.CheckConstraint(
            "model_type IN ('MOVING_AVERAGE', 'RANDOM_FOREST', 'XGBOOST')",
            name="ck_model_versions_type",
        ),
        sa.CheckConstraint(
            "data_type IN ('SYNTHETIC', 'REAL')", name="ck_model_versions_data_type"
        ),
        sa.CheckConstraint(
            "training_end_date >= training_start_date",
            name="ck_model_versions_training_dates",
        ),
        sa.UniqueConstraint(
            "cooperative_id", "version", name="uq_model_versions_cooperative_version"
        ),
        sa.UniqueConstraint("task_id", name="uq_model_versions_task"),
    )
    op.create_index(
        "uq_model_versions_active_scope",
        "model_versions",
        ["cooperative_id", "warehouse_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_table(
        "forecast_results",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id",
            UUID,
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            UUID,
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "model_version_id",
            UUID,
            sa.ForeignKey("model_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "task_id", UUID, sa.ForeignKey("task_records.id", ondelete="SET NULL")
        ),
        sa.Column("horizon_days", sa.SmallInteger(), nullable=False),
        sa.Column("forecast_start_date", sa.Date(), nullable=False),
        sa.Column("forecast_end_date", sa.Date(), nullable=False),
        sa.Column("predicted_demand", sa.Numeric(14, 3), nullable=False),
        sa.Column("current_stock", sa.Numeric(14, 3), nullable=False),
        sa.Column("recommended_replenishment", sa.Numeric(14, 3), nullable=False),
        sa.Column("data_type", sa.String(16), nullable=False),
        sa.Column(
            "metrics", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "important_factors",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("limitation_notice", sa.String(500), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "horizon_days IN (7, 30)", name="ck_forecast_results_horizon"
        ),
        sa.CheckConstraint(
            "forecast_end_date = forecast_start_date + (horizon_days - 1)",
            name="ck_forecast_results_date_range",
        ),
        sa.CheckConstraint(
            "predicted_demand >= 0 AND current_stock >= 0 "
            "AND recommended_replenishment >= 0",
            name="ck_forecast_results_quantities",
        ),
        sa.CheckConstraint(
            "data_type IN ('SYNTHETIC', 'REAL')", name="ck_forecast_results_data_type"
        ),
        sa.UniqueConstraint("task_id", name="uq_forecast_results_task"),
    )
    op.create_index(
        "ix_forecast_results_scope_generated",
        "forecast_results",
        [
            "cooperative_id",
            "warehouse_id",
            "product_id",
            sa.text("generated_at DESC"),
        ],
    )
    op.create_table(
        "forecast_points",
        _id_column(),
        sa.Column(
            "forecast_result_id",
            UUID,
            sa.ForeignKey("forecast_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("predicted_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("lower_bound", sa.Numeric(14, 3), nullable=False),
        sa.Column("upper_bound", sa.Numeric(14, 3), nullable=False),
        sa.CheckConstraint(
            "predicted_quantity >= 0 AND lower_bound >= 0 AND upper_bound >= 0",
            name="ck_forecast_points_nonnegative",
        ),
        sa.CheckConstraint(
            "lower_bound <= predicted_quantity AND predicted_quantity <= upper_bound",
            name="ck_forecast_points_bounds",
        ),
        sa.UniqueConstraint(
            "forecast_result_id", "forecast_date", name="uq_forecast_points_result_date"
        ),
    )
    op.create_table(
        "audit_logs",
        _id_column(),
        sa.Column(
            "cooperative_id",
            UUID,
            sa.ForeignKey("cooperatives.id", ondelete="RESTRICT"),
        ),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("module", sa.String(32), nullable=False),
        sa.Column("object_type", sa.String(64), nullable=False),
        sa.Column("object_id", UUID),
        sa.Column("result", sa.String(16), nullable=False),
        sa.Column("request_id", sa.String(64)),
        sa.Column("ip_address", postgresql.INET()),
        sa.Column("user_agent", sa.String(500)),
        sa.Column(
            "detail", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        _created_at_column(),
        sa.CheckConstraint(
            "result IN ('SUCCESS', 'FAILURE')", name="ck_audit_logs_result"
        ),
    )
    op.create_index(
        "ix_audit_logs_cooperative_created",
        "audit_logs",
        ["cooperative_id", sa.text("created_at DESC")],
    )

    op.execute(
        """
        CREATE FUNCTION prevent_immutable_record_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION '% records are immutable', TG_TABLE_NAME;
        END;
        $$
        """
    )
    for table_name in (
        "inventory_transactions",
        "alert_handling_logs",
        "audit_logs",
    ):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table_name}_immutable
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_mutation()
            """
        )


def downgrade() -> None:
    """逆序删除V1数据库结构。"""
    for table_name in (
        "inventory_transactions",
        "alert_handling_logs",
        "audit_logs",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table_name}_immutable ON {table_name}")
    op.execute("DROP FUNCTION IF EXISTS prevent_immutable_record_mutation()")

    op.drop_table("audit_logs")
    op.drop_table("forecast_points")
    op.drop_table("forecast_results")
    op.drop_table("model_versions")
    op.drop_table("idempotency_records")
    op.drop_table("task_records")
    op.drop_table("alert_handling_logs")
    op.drop_table("alerts")
    op.drop_table("alert_rules")
    op.drop_table("trace_events")
    op.drop_table("inventory_transactions")
    op.drop_table("inventory_operations")
    op.drop_table("inventories")
    op.drop_table("inspection_files")
    op.drop_table("quality_inspection_items")
    op.drop_table("quality_inspections")
    op.drop_table("files")
    op.drop_table("batches")
    op.drop_table("products")
    op.drop_table("product_categories")
    op.drop_table("user_warehouses")
    op.drop_table("warehouses")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("cooperatives")

    # pgcrypto可能由同一数据库中的其他应用使用，因此降级时不删除扩展。
