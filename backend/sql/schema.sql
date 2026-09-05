-- 农产品批次追溯与智能库存预警系统 V1 数据库结构
-- 本文件由 Alembic 初始迁移离线生成；结构变更应先修改迁移，再重新生成本文件。
-- 执行目标：PostgreSQL 15+。本文件只创建结构，不包含演示数据。

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> e4f3c0ebc976

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE cooperatives (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    code VARCHAR(32) NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    contact_name VARCHAR(50), 
    contact_phone VARCHAR(20), 
    address VARCHAR(255), 
    status VARCHAR(16) DEFAULT 'ACTIVE' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_cooperatives_status CHECK (status IN ('ACTIVE', 'INACTIVE')), 
    CONSTRAINT uq_cooperatives_code UNIQUE (code)
);

CREATE TABLE roles (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    code VARCHAR(32) NOT NULL, 
    name VARCHAR(50) NOT NULL, 
    description VARCHAR(255), 
    is_system BOOLEAN DEFAULT false NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_roles_code UNIQUE (code)
);

CREATE TABLE permissions (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    code VARCHAR(64) NOT NULL, 
    name VARCHAR(80) NOT NULL, 
    module VARCHAR(32) NOT NULL, 
    description VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_permissions_code UNIQUE (code)
);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL, 
    permission_id UUID NOT NULL, 
    PRIMARY KEY (role_id, permission_id), 
    FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
    FOREIGN KEY(permission_id) REFERENCES permissions (id) ON DELETE CASCADE
);

CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID, 
    role_id UUID NOT NULL, 
    username VARCHAR(50) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    real_name VARCHAR(50) NOT NULL, 
    phone VARCHAR(20), 
    status VARCHAR(16) DEFAULT 'ACTIVE' NOT NULL, 
    last_login_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_users_username_lower CHECK (username = lower(username)), 
    CONSTRAINT ck_users_status CHECK (status IN ('ACTIVE', 'LOCKED', 'INACTIVE')), 
    CONSTRAINT uq_users_username UNIQUE (username), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE RESTRICT
);

CREATE INDEX ix_users_cooperative_status ON users (cooperative_id, status);

CREATE TABLE warehouses (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    code VARCHAR(32) NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    address VARCHAR(255), 
    manager_name VARCHAR(50), 
    status VARCHAR(16) DEFAULT 'ACTIVE' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_warehouses_status CHECK (status IN ('ACTIVE', 'INACTIVE')), 
    CONSTRAINT uq_warehouses_cooperative_code UNIQUE (cooperative_id, code), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT
);

CREATE INDEX ix_warehouses_cooperative_status ON warehouses (cooperative_id, status);

CREATE TABLE user_warehouses (
    user_id UUID NOT NULL, 
    warehouse_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (user_id, warehouse_id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE CASCADE
);

CREATE TABLE product_categories (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    code VARCHAR(32) NOT NULL, 
    name VARCHAR(80) NOT NULL, 
    description VARCHAR(255), 
    is_active BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_product_categories_cooperative_code UNIQUE (cooperative_id, code), 
    CONSTRAINT uq_product_categories_cooperative_name UNIQUE (cooperative_id, name), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT
);

CREATE TABLE products (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    category_id UUID NOT NULL, 
    code VARCHAR(32) NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    unit VARCHAR(20) NOT NULL, 
    shelf_life_days INTEGER NOT NULL, 
    safety_stock NUMERIC(14, 3) DEFAULT '0' NOT NULL, 
    is_active BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_products_shelf_life CHECK (shelf_life_days > 0), 
    CONSTRAINT ck_products_safety_stock CHECK (safety_stock >= 0), 
    CONSTRAINT uq_products_cooperative_code UNIQUE (cooperative_id, code), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(category_id) REFERENCES product_categories (id) ON DELETE RESTRICT
);

CREATE INDEX ix_products_cooperative_active_name ON products (cooperative_id, is_active, name);

CREATE TABLE batches (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    product_id UUID NOT NULL, 
    batch_no VARCHAR(64) NOT NULL, 
    trace_code VARCHAR(64) NOT NULL, 
    origin VARCHAR(255) NOT NULL, 
    production_date DATE NOT NULL, 
    expiry_date DATE NOT NULL, 
    responsible_person VARCHAR(50), 
    status VARCHAR(20) DEFAULT 'CREATED' NOT NULL, 
    created_by UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_batches_date_order CHECK (expiry_date >= production_date), 
    CONSTRAINT ck_batches_status CHECK (status IN ('CREATED', 'IN_STOCK', 'DEPLETED', 'BLOCKED', 'EXPIRED')), 
    CONSTRAINT uq_batches_batch_no UNIQUE (batch_no), 
    CONSTRAINT uq_batches_trace_code UNIQUE (trace_code), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_batches_cooperative_product_production ON batches (cooperative_id, product_id, production_date);

CREATE INDEX ix_batches_cooperative_expiry ON batches (cooperative_id, expiry_date);

CREATE TABLE files (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    original_name VARCHAR(255) NOT NULL, 
    storage_key VARCHAR(255) NOT NULL, 
    mime_type VARCHAR(100) NOT NULL, 
    size_bytes BIGINT NOT NULL, 
    sha256 VARCHAR(64) NOT NULL, 
    uploaded_by UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_files_size_positive CHECK (size_bytes > 0), 
    CONSTRAINT uq_files_storage_key UNIQUE (storage_key), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(uploaded_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TABLE quality_inspections (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    batch_id UUID NOT NULL, 
    inspection_no VARCHAR(64) NOT NULL, 
    inspected_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    inspector_id UUID NOT NULL, 
    conclusion VARCHAR(16) DEFAULT 'PENDING' NOT NULL, 
    remarks VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_quality_inspections_conclusion CHECK (conclusion IN ('PENDING', 'PASSED', 'FAILED')), 
    CONSTRAINT uq_quality_inspections_cooperative_no UNIQUE (cooperative_id, inspection_no), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(batch_id) REFERENCES batches (id) ON DELETE RESTRICT, 
    FOREIGN KEY(inspector_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_quality_inspections_batch_time ON quality_inspections (batch_id, inspected_at DESC);

CREATE TABLE quality_inspection_items (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    inspection_id UUID NOT NULL, 
    item_name VARCHAR(100) NOT NULL, 
    standard_value VARCHAR(100) NOT NULL, 
    result_value VARCHAR(100) NOT NULL, 
    is_qualified BOOLEAN NOT NULL, 
    sort_order INTEGER DEFAULT '0' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_inspection_items_sort_order CHECK (sort_order >= 0), 
    CONSTRAINT uq_inspection_items_name UNIQUE (inspection_id, item_name), 
    FOREIGN KEY(inspection_id) REFERENCES quality_inspections (id) ON DELETE CASCADE
);

CREATE TABLE inspection_files (
    inspection_id UUID NOT NULL, 
    file_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (inspection_id, file_id), 
    FOREIGN KEY(inspection_id) REFERENCES quality_inspections (id) ON DELETE CASCADE, 
    FOREIGN KEY(file_id) REFERENCES files (id) ON DELETE CASCADE
);

CREATE TABLE inventories (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    warehouse_id UUID NOT NULL, 
    batch_id UUID NOT NULL, 
    quantity NUMERIC(14, 3) DEFAULT '0' NOT NULL, 
    locked_quantity NUMERIC(14, 3) DEFAULT '0' NOT NULL, 
    version INTEGER DEFAULT '0' NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_inventories_quantity CHECK (quantity >= 0), 
    CONSTRAINT ck_inventories_locked_quantity CHECK (locked_quantity >= 0 AND locked_quantity <= quantity), 
    CONSTRAINT ck_inventories_version CHECK (version >= 0), 
    CONSTRAINT uq_inventories_warehouse_batch UNIQUE (warehouse_id, batch_id), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
    FOREIGN KEY(batch_id) REFERENCES batches (id) ON DELETE RESTRICT
);

CREATE INDEX ix_inventories_cooperative_warehouse ON inventories (cooperative_id, warehouse_id);

CREATE TABLE inventory_operations (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    operation_no VARCHAR(64) NOT NULL, 
    operation_type VARCHAR(24) NOT NULL, 
    source_warehouse_id UUID, 
    destination_warehouse_id UUID, 
    external_reference VARCHAR(100), 
    reason VARCHAR(500), 
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    status VARCHAR(16) DEFAULT 'COMPLETED' NOT NULL, 
    created_by UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_inventory_operations_type CHECK (operation_type IN ('INBOUND', 'OUTBOUND', 'ADJUSTMENT', 'DAMAGE', 'TRANSFER')), 
    CONSTRAINT ck_inventory_operations_status CHECK (status IN ('COMPLETED', 'REVERSED')), 
    CONSTRAINT ck_inventory_operations_transfer_warehouses CHECK ((operation_type = 'TRANSFER' AND source_warehouse_id IS NOT NULL AND destination_warehouse_id IS NOT NULL AND source_warehouse_id <> destination_warehouse_id) OR (operation_type <> 'TRANSFER' AND source_warehouse_id IS NULL AND destination_warehouse_id IS NULL)), 
    CONSTRAINT uq_inventory_operations_no UNIQUE (operation_no), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(source_warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
    FOREIGN KEY(destination_warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_inventory_operations_external_reference ON inventory_operations (cooperative_id, external_reference) WHERE external_reference IS NOT NULL;

CREATE TABLE inventory_transactions (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    operation_id UUID NOT NULL, 
    warehouse_id UUID NOT NULL, 
    batch_id UUID NOT NULL, 
    transaction_type VARCHAR(24) NOT NULL, 
    quantity_delta NUMERIC(14, 3) NOT NULL, 
    quantity_before NUMERIC(14, 3) NOT NULL, 
    quantity_after NUMERIC(14, 3) NOT NULL, 
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    created_by UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_inventory_transactions_type CHECK (transaction_type IN ('INBOUND', 'OUTBOUND', 'ADJUSTMENT', 'DAMAGE', 'TRANSFER_OUT', 'TRANSFER_IN')), 
    CONSTRAINT ck_inventory_transactions_nonnegative CHECK (quantity_before >= 0 AND quantity_after >= 0), 
    CONSTRAINT ck_inventory_transactions_delta_nonzero CHECK (quantity_delta <> 0), 
    CONSTRAINT ck_inventory_transactions_balance CHECK (quantity_before + quantity_delta = quantity_after), 
    CONSTRAINT ck_inventory_transactions_delta_direction CHECK ((transaction_type IN ('INBOUND', 'TRANSFER_IN') AND quantity_delta > 0) OR (transaction_type IN ('OUTBOUND', 'DAMAGE', 'TRANSFER_OUT') AND quantity_delta < 0) OR transaction_type = 'ADJUSTMENT'), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(operation_id) REFERENCES inventory_operations (id) ON DELETE RESTRICT, 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
    FOREIGN KEY(batch_id) REFERENCES batches (id) ON DELETE RESTRICT, 
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_inventory_transactions_warehouse_time ON inventory_transactions (cooperative_id, warehouse_id, occurred_at DESC);

CREATE INDEX ix_inventory_transactions_batch_time ON inventory_transactions (batch_id, occurred_at);

CREATE TABLE trace_events (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    batch_id UUID NOT NULL, 
    event_type VARCHAR(32) NOT NULL, 
    title VARCHAR(100) NOT NULL, 
    description VARCHAR(500), 
    event_time TIMESTAMP WITH TIME ZONE NOT NULL, 
    source_type VARCHAR(32), 
    source_id UUID, 
    public_data JSONB DEFAULT '{}'::jsonb NOT NULL, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_trace_events_type CHECK (event_type IN ('PRODUCTION', 'INSPECTION', 'INBOUND', 'OUTBOUND', 'TRANSFER', 'OTHER')), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(batch_id) REFERENCES batches (id) ON DELETE RESTRICT, 
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_trace_events_batch_time ON trace_events (batch_id, event_time, id);

CREATE TABLE alert_rules (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    warehouse_id UUID, 
    product_id UUID, 
    alert_type VARCHAR(24) NOT NULL, 
    threshold_quantity NUMERIC(14, 3), 
    threshold_days INTEGER, 
    turnover_days INTEGER, 
    severity VARCHAR(16) NOT NULL, 
    is_enabled BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_alert_rules_type CHECK (alert_type IN ('LOW_STOCK', 'NEAR_EXPIRY', 'OVERSTOCK', 'QUALITY_FAILED')), 
    CONSTRAINT ck_alert_rules_severity CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')), 
    CONSTRAINT ck_alert_rules_threshold_quantity CHECK (threshold_quantity IS NULL OR threshold_quantity >= 0), 
    CONSTRAINT ck_alert_rules_threshold_days CHECK (threshold_days IS NULL OR threshold_days >= 0), 
    CONSTRAINT ck_alert_rules_turnover_days CHECK (turnover_days IS NULL OR turnover_days >= 0), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
    FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT
);

CREATE INDEX ix_alert_rules_scope ON alert_rules (cooperative_id, warehouse_id, product_id, alert_type);

CREATE TABLE alerts (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    rule_id UUID, 
    alert_type VARCHAR(24) NOT NULL, 
    severity VARCHAR(16) NOT NULL, 
    status VARCHAR(16) DEFAULT 'PENDING' NOT NULL, 
    warehouse_id UUID, 
    product_id UUID, 
    batch_id UUID, 
    dedupe_key VARCHAR(160) NOT NULL, 
    title VARCHAR(120) NOT NULL, 
    message VARCHAR(500) NOT NULL, 
    evidence JSONB DEFAULT '{}'::jsonb NOT NULL, 
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    resolved_at TIMESTAMP WITH TIME ZONE, 
    assignee_id UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_alerts_type CHECK (alert_type IN ('LOW_STOCK', 'NEAR_EXPIRY', 'OVERSTOCK', 'QUALITY_FAILED')), 
    CONSTRAINT ck_alerts_severity CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')), 
    CONSTRAINT ck_alerts_status CHECK (status IN ('PENDING', 'PROCESSING', 'RESOLVED', 'IGNORED')), 
    CONSTRAINT ck_alerts_resolution_time CHECK ((status IN ('PENDING', 'PROCESSING') AND resolved_at IS NULL) OR (status IN ('RESOLVED', 'IGNORED') AND resolved_at IS NOT NULL)), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(rule_id) REFERENCES alert_rules (id) ON DELETE SET NULL, 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
    FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    FOREIGN KEY(batch_id) REFERENCES batches (id) ON DELETE RESTRICT, 
    FOREIGN KEY(assignee_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX uq_alerts_active_dedupe ON alerts (cooperative_id, dedupe_key) WHERE status IN ('PENDING', 'PROCESSING');

CREATE INDEX ix_alerts_workbench ON alerts (cooperative_id, status, severity, detected_at DESC);

CREATE TABLE alert_handling_logs (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    alert_id UUID NOT NULL, 
    operator_id UUID NOT NULL, 
    from_status VARCHAR(16) NOT NULL, 
    to_status VARCHAR(16) NOT NULL, 
    comment VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_alert_handling_logs_from_status CHECK (from_status IN ('PENDING', 'PROCESSING', 'RESOLVED', 'IGNORED')), 
    CONSTRAINT ck_alert_handling_logs_to_status CHECK (to_status IN ('PENDING', 'PROCESSING', 'RESOLVED', 'IGNORED')), 
    FOREIGN KEY(alert_id) REFERENCES alerts (id) ON DELETE RESTRICT, 
    FOREIGN KEY(operator_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_alert_handling_logs_alert_time ON alert_handling_logs (alert_id, created_at);

CREATE TABLE task_records (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID, 
    task_type VARCHAR(32) NOT NULL, 
    celery_task_id VARCHAR(64) NOT NULL, 
    status VARCHAR(16) DEFAULT 'PENDING' NOT NULL, 
    progress SMALLINT DEFAULT '0' NOT NULL, 
    request_payload JSONB DEFAULT '{}'::jsonb NOT NULL, 
    result_payload JSONB, 
    error_code VARCHAR(64), 
    error_message VARCHAR(500), 
    requested_by UUID, 
    started_at TIMESTAMP WITH TIME ZONE, 
    finished_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_task_records_status CHECK (status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILURE', 'RETRY')), 
    CONSTRAINT ck_task_records_progress CHECK (progress BETWEEN 0 AND 100), 
    CONSTRAINT ck_task_records_time_order_presence CHECK (finished_at IS NULL OR started_at IS NOT NULL), 
    CONSTRAINT ck_task_records_time_order CHECK (finished_at IS NULL OR finished_at >= started_at), 
    CONSTRAINT uq_task_records_celery_id UNIQUE (celery_task_id), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(requested_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_task_records_cooperative_created ON task_records (cooperative_id, created_at DESC);

CREATE TABLE idempotency_records (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    endpoint VARCHAR(160) NOT NULL, 
    idempotency_key VARCHAR(128) NOT NULL, 
    request_hash VARCHAR(64) NOT NULL, 
    status VARCHAR(16) DEFAULT 'PROCESSING' NOT NULL, 
    response_status SMALLINT, 
    response_body JSONB, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_idempotency_records_status CHECK (status IN ('PROCESSING', 'COMPLETED', 'FAILED')), 
    CONSTRAINT ck_idempotency_records_response_status CHECK (response_status IS NULL OR response_status BETWEEN 100 AND 599), 
    CONSTRAINT ck_idempotency_records_expiry CHECK (expires_at > created_at), 
    CONSTRAINT uq_idempotency_records_request UNIQUE (user_id, endpoint, idempotency_key), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_idempotency_records_expiry ON idempotency_records (expires_at);

CREATE TABLE model_versions (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    warehouse_id UUID NOT NULL, 
    product_id UUID NOT NULL, 
    task_id UUID, 
    model_type VARCHAR(24) NOT NULL, 
    version VARCHAR(64) NOT NULL, 
    artifact_path VARCHAR(255), 
    data_type VARCHAR(16) NOT NULL, 
    training_start_date DATE NOT NULL, 
    training_end_date DATE NOT NULL, 
    random_seed INTEGER NOT NULL, 
    parameters JSONB DEFAULT '{}'::jsonb NOT NULL, 
    metrics JSONB DEFAULT '{}'::jsonb NOT NULL, 
    is_active BOOLEAN DEFAULT false NOT NULL, 
    created_by UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_model_versions_type CHECK (model_type IN ('MOVING_AVERAGE', 'RANDOM_FOREST', 'XGBOOST')), 
    CONSTRAINT ck_model_versions_data_type CHECK (data_type IN ('SYNTHETIC', 'REAL')), 
    CONSTRAINT ck_model_versions_training_dates CHECK (training_end_date >= training_start_date), 
    CONSTRAINT uq_model_versions_cooperative_version UNIQUE (cooperative_id, version), 
    CONSTRAINT uq_model_versions_task UNIQUE (task_id), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
    FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    FOREIGN KEY(task_id) REFERENCES task_records (id) ON DELETE SET NULL, 
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_model_versions_active_scope ON model_versions (cooperative_id, warehouse_id, product_id) WHERE is_active = true;

CREATE TABLE forecast_results (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID NOT NULL, 
    warehouse_id UUID NOT NULL, 
    product_id UUID NOT NULL, 
    model_version_id UUID NOT NULL, 
    task_id UUID, 
    horizon_days SMALLINT NOT NULL, 
    forecast_start_date DATE NOT NULL, 
    forecast_end_date DATE NOT NULL, 
    predicted_demand NUMERIC(14, 3) NOT NULL, 
    current_stock NUMERIC(14, 3) NOT NULL, 
    recommended_replenishment NUMERIC(14, 3) NOT NULL, 
    data_type VARCHAR(16) NOT NULL, 
    metrics JSONB DEFAULT '{}'::jsonb NOT NULL, 
    important_factors JSONB DEFAULT '[]'::jsonb NOT NULL, 
    limitation_notice VARCHAR(500) NOT NULL, 
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_forecast_results_horizon CHECK (horizon_days IN (7, 30)), 
    CONSTRAINT ck_forecast_results_date_range CHECK (forecast_end_date = forecast_start_date + (horizon_days - 1)), 
    CONSTRAINT ck_forecast_results_quantities CHECK (predicted_demand >= 0 AND current_stock >= 0 AND recommended_replenishment >= 0), 
    CONSTRAINT ck_forecast_results_data_type CHECK (data_type IN ('SYNTHETIC', 'REAL')), 
    CONSTRAINT uq_forecast_results_task UNIQUE (task_id), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE RESTRICT, 
    FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    FOREIGN KEY(model_version_id) REFERENCES model_versions (id) ON DELETE RESTRICT, 
    FOREIGN KEY(task_id) REFERENCES task_records (id) ON DELETE SET NULL
);

CREATE INDEX ix_forecast_results_scope_generated ON forecast_results (cooperative_id, warehouse_id, product_id, generated_at DESC);

CREATE TABLE forecast_points (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    forecast_result_id UUID NOT NULL, 
    forecast_date DATE NOT NULL, 
    predicted_quantity NUMERIC(14, 3) NOT NULL, 
    lower_bound NUMERIC(14, 3) NOT NULL, 
    upper_bound NUMERIC(14, 3) NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_forecast_points_nonnegative CHECK (predicted_quantity >= 0 AND lower_bound >= 0 AND upper_bound >= 0), 
    CONSTRAINT ck_forecast_points_bounds CHECK (lower_bound <= predicted_quantity AND predicted_quantity <= upper_bound), 
    CONSTRAINT uq_forecast_points_result_date UNIQUE (forecast_result_id, forecast_date), 
    FOREIGN KEY(forecast_result_id) REFERENCES forecast_results (id) ON DELETE CASCADE
);

CREATE TABLE audit_logs (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    cooperative_id UUID, 
    user_id UUID, 
    action VARCHAR(64) NOT NULL, 
    module VARCHAR(32) NOT NULL, 
    object_type VARCHAR(64) NOT NULL, 
    object_id UUID, 
    result VARCHAR(16) NOT NULL, 
    request_id VARCHAR(64), 
    ip_address INET, 
    user_agent VARCHAR(500), 
    detail JSONB DEFAULT '{}'::jsonb NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_audit_logs_result CHECK (result IN ('SUCCESS', 'FAILURE')), 
    FOREIGN KEY(cooperative_id) REFERENCES cooperatives (id) ON DELETE RESTRICT, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_audit_logs_cooperative_created ON audit_logs (cooperative_id, created_at DESC);

CREATE FUNCTION prevent_immutable_record_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION '% records are immutable', TG_TABLE_NAME;
        END;
        $$;

CREATE TRIGGER trg_inventory_transactions_immutable
            BEFORE UPDATE OR DELETE ON inventory_transactions
            FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_mutation();

CREATE TRIGGER trg_alert_handling_logs_immutable
            BEFORE UPDATE OR DELETE ON alert_handling_logs
            FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_mutation();

CREATE TRIGGER trg_audit_logs_immutable
            BEFORE UPDATE OR DELETE ON audit_logs
            FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_mutation();

INSERT INTO alembic_version (version_num) VALUES ('e4f3c0ebc976') RETURNING alembic_version.version_num;

COMMIT;

