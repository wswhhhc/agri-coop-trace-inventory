"""生成可复现的虚构演示数据SQL。"""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Iterable, Sequence
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from faker import Faker

from app.core.config import DemoSettings

DEFAULT_SEED = DemoSettings().demo_data_seed
DEMO_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$Jr7nDhBa/TJu8djiucnYmQ$"
    "PpfaZDyJYSlP+Bgnlm/9Oz7/mPkMsPpg4DDTEibL50k"
)
AS_OF_DATE = date(2026, 9, 4)
TZ_CST = timezone(timedelta(hours=8))
GENERATED_AT = datetime.combine(AS_OF_DATE, time(9), TZ_CST)

Row = dict[str, Any]
TableRows = tuple[str, list[Row]]


def get_demo_password() -> str:
    """读取本地演示账号密码；演示 SQL 仍使用固定哈希以保持可复现。"""
    password = DemoSettings().demo_password
    if password is None:
        raise RuntimeError("DEMO_PASSWORD 未配置，请在 backend/.env 中填写")
    return password.get_secret_value()

PERMISSION_SPECS = (
    ("cooperative:manage", "管理合作社", "organization"),
    ("user:manage", "管理用户", "identity"),
    ("warehouse:manage", "管理仓库", "organization"),
    ("product:manage", "管理产品", "catalog"),
    ("batch:manage", "管理批次", "batch"),
    ("inventory:read", "查看库存", "inventory"),
    ("inventory:write", "办理库存业务", "inventory"),
    ("trace:read", "查看追溯", "traceability"),
    ("alert:read", "查看预警", "alerting"),
    ("alert:handle", "处理预警", "alerting"),
    ("model:read", "查看预测模型", "forecasting"),
    ("model:manage", "管理预测模型", "forecasting"),
    ("audit:read", "查看审计", "audit"),
)


def permission_codes_by_role() -> dict[str, list[str]]:
    """返回与需求文档一致的演示角色权限边界。"""
    all_codes = [code for code, _, _ in PERMISSION_SPECS]
    return {
        "SYSTEM_ADMIN": [
            "cooperative:manage",
            "user:manage",
            "inventory:read",
            "trace:read",
            "alert:read",
            "model:read",
            "audit:read",
        ],
        "COOPERATIVE_ADMIN": [
            code for code in all_codes if code != "cooperative:manage"
        ],
        "WAREHOUSE_STAFF": [
            "batch:manage",
            "inventory:read",
            "inventory:write",
            "trace:read",
            "alert:read",
            "alert:handle",
            "model:read",
            "audit:read",
        ],
    }


def _uuid(seed: int, label: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"agri-trace-demo:{seed}:{label}")


def _decimal(value: float, digits: int = 3) -> Decimal:
    quantum = Decimal(1).scaleb(-digits)
    return Decimal(str(value)).quantize(quantum)


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        text = value.isoformat(timespec="seconds")
    elif isinstance(value, date):
        text = value.isoformat()
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        escaped = text.replace("'", "''")
        return f"'{escaped}'::jsonb"
    else:
        text = str(value)
    escaped = text.replace("'", "''")
    return f"'{escaped}'"


def _render_insert(table: str, rows: Sequence[Row]) -> str:
    if not rows:
        return ""
    columns = list(rows[0])
    values = []
    for row in rows:
        if list(row) != columns:
            raise ValueError(f"{table}的行字段顺序不一致")
        values.append(
            "    (" + ", ".join(_sql_literal(row[column]) for column in columns) + ")"
        )
    return (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n"
        + ",\n".join(values)
        + "\nON CONFLICT DO NOTHING;"
    )


def _at(day: date, hour: int = 9) -> datetime:
    return datetime.combine(day, time(hour), TZ_CST)


def _base_rows(
    seed: int, rng: random.Random, fake: Faker
) -> tuple[list[TableRows], dict[str, Any]]:
    role_ids = {
        code: _uuid(seed, f"role:{code}")
        for code in ("SYSTEM_ADMIN", "COOPERATIVE_ADMIN", "WAREHOUSE_STAFF")
    }
    roles = [
        {
            "id": role_ids["SYSTEM_ADMIN"],
            "code": "SYSTEM_ADMIN",
            "name": "系统管理员",
            "description": "维护平台合作社、角色权限并查看全局审计",
            "is_system": True,
            "created_at": GENERATED_AT,
        },
        {
            "id": role_ids["COOPERATIVE_ADMIN"],
            "code": "COOPERATIVE_ADMIN",
            "name": "合作社管理员",
            "description": "管理本合作社人员、产品、库存、预警和模型",
            "is_system": True,
            "created_at": GENERATED_AT,
        },
        {
            "id": role_ids["WAREHOUSE_STAFF"],
            "code": "WAREHOUSE_STAFF",
            "name": "仓库工作人员",
            "description": "在授权仓库执行批次和库存操作",
            "is_system": True,
            "created_at": GENERATED_AT,
        },
    ]

    permission_specs = PERMISSION_SPECS
    permission_ids = {
        code: _uuid(seed, f"permission:{code}") for code, _, _ in permission_specs
    }
    permissions = [
        {
            "id": permission_ids[code],
            "code": code,
            "name": name,
            "module": module,
            "description": f"演示权限：{name}",
            "created_at": GENERATED_AT,
        }
        for code, name, module in permission_specs
    ]
    role_permissions_by_role = permission_codes_by_role()
    role_permissions: list[Row] = []
    for role_code, codes in role_permissions_by_role.items():
        role_permissions.extend(
            {"role_id": role_ids[role_code], "permission_id": permission_ids[code]}
            for code in codes
        )

    cooperative_specs = [
        ("DEMO-FH", "松岭丰禾农业合作社（演示）", "吉林省演示市松岭农业园区1号"),
        ("DEMO-WY", "北辰沃野农业合作社（演示）", "吉林省演示市北辰农业园区2号"),
    ]
    cooperatives = []
    cooperative_ids: list[UUID] = []
    for index, (code, name, address) in enumerate(cooperative_specs):
        cooperative_id = _uuid(seed, f"cooperative:{index}")
        cooperative_ids.append(cooperative_id)
        cooperatives.append(
            {
                "id": cooperative_id,
                "code": code,
                "name": name,
                "contact_name": fake.name(),
                "contact_phone": f"139{rng.randint(0, 99_999_999):08d}",
                "address": address,
                "status": "ACTIVE",
                "created_at": GENERATED_AT,
                "updated_at": GENERATED_AT,
            }
        )

    users = [
        {
            "id": _uuid(seed, "user:sysadmin"),
            "cooperative_id": None,
            "role_id": role_ids["SYSTEM_ADMIN"],
            "username": "sysadmin",
            "password_hash": DEMO_PASSWORD_HASH,
            "real_name": "系统演示管理员",
            "phone": None,
            "status": "ACTIVE",
            "last_login_at": GENERATED_AT,
            "created_at": GENERATED_AT,
            "updated_at": GENERATED_AT,
        }
    ]
    cooperative_admin_ids: list[UUID] = []
    staff_ids: list[list[UUID]] = []
    for coop_index, cooperative_id in enumerate(cooperative_ids, start=1):
        admin_id = _uuid(seed, f"user:coop:{coop_index}:admin")
        cooperative_admin_ids.append(admin_id)
        users.append(
            {
                "id": admin_id,
                "cooperative_id": cooperative_id,
                "role_id": role_ids["COOPERATIVE_ADMIN"],
                "username": f"coop{coop_index}_admin",
                "password_hash": DEMO_PASSWORD_HASH,
                "real_name": f"演示管理员{coop_index}",
                "phone": f"138{rng.randint(0, 99_999_999):08d}",
                "status": "ACTIVE",
                "last_login_at": GENERATED_AT - timedelta(hours=coop_index),
                "created_at": GENERATED_AT,
                "updated_at": GENERATED_AT,
            }
        )
        coop_staff_ids = []
        for staff_index in range(1, 3):
            staff_id = _uuid(seed, f"user:coop:{coop_index}:staff:{staff_index}")
            coop_staff_ids.append(staff_id)
            users.append(
                {
                    "id": staff_id,
                    "cooperative_id": cooperative_id,
                    "role_id": role_ids["WAREHOUSE_STAFF"],
                    "username": f"coop{coop_index}_staff{staff_index}",
                    "password_hash": DEMO_PASSWORD_HASH,
                    "real_name": fake.name(),
                    "phone": f"137{rng.randint(0, 99_999_999):08d}",
                    "status": "ACTIVE",
                    "last_login_at": GENERATED_AT - timedelta(days=staff_index),
                    "created_at": GENERATED_AT,
                    "updated_at": GENERATED_AT,
                }
            )
        staff_ids.append(coop_staff_ids)

    warehouse_names = (("中心仓", "冷链仓"), ("东部仓", "保鲜仓"))
    warehouses = []
    warehouse_ids: list[list[UUID]] = []
    user_warehouses = []
    for coop_index, cooperative_id in enumerate(cooperative_ids):
        coop_warehouses = []
        for warehouse_index, name in enumerate(warehouse_names[coop_index], start=1):
            warehouse_id = _uuid(seed, f"warehouse:{coop_index}:{warehouse_index}")
            coop_warehouses.append(warehouse_id)
            warehouses.append(
                {
                    "id": warehouse_id,
                    "cooperative_id": cooperative_id,
                    "code": f"WH-{coop_index + 1:02d}-{warehouse_index:02d}",
                    "name": name,
                    "address": f"吉林省演示市{coop_index + 1}区农业路{warehouse_index}号",
                    "manager_name": users[2 + coop_index * 3 + warehouse_index - 1][
                        "real_name"
                    ],
                    "status": "ACTIVE",
                    "created_at": GENERATED_AT,
                    "updated_at": GENERATED_AT,
                }
            )
            user_warehouses.append(
                {
                    "user_id": staff_ids[coop_index][warehouse_index - 1],
                    "warehouse_id": warehouse_id,
                    "created_at": GENERATED_AT,
                }
            )
        warehouse_ids.append(coop_warehouses)

    tables: list[TableRows] = [
        ("cooperatives", cooperatives),
        ("roles", roles),
        ("permissions", permissions),
        ("role_permissions", role_permissions),
        ("users", users),
        ("warehouses", warehouses),
        ("user_warehouses", user_warehouses),
    ]
    context = {
        "cooperative_ids": cooperative_ids,
        "cooperative_admin_ids": cooperative_admin_ids,
        "staff_ids": staff_ids,
        "warehouse_ids": warehouse_ids,
        "user_cooperative_ids": {user["id"]: user["cooperative_id"] for user in users},
    }
    return tables, context


def _catalog_rows(
    seed: int, rng: random.Random, context: dict[str, Any]
) -> tuple[list[TableRows], dict[str, Any]]:
    category_specs = (("GRAIN", "粮食作物"), ("VEGETABLE", "蔬菜作物"))
    product_specs = (
        ("RICE", "优质粳米", "千克", 365, 180, 13.0),
        ("CORN", "鲜食玉米", "千克", 30, 120, 18.0),
        ("SOY", "非转基因黄豆", "千克", 300, 150, 11.0),
        ("POTATO", "红皮马铃薯", "千克", 90, 130, 15.0),
    )
    categories = []
    products = []
    batches = []
    files = []
    inspections = []
    inspection_items = []
    inspection_files = []
    product_ids: list[list[UUID]] = []
    batch_ids: dict[tuple[int, int, int], UUID] = {}
    failed_batch_keys = {(0, 3, 2), (1, 3, 2)}

    for coop_index, cooperative_id in enumerate(context["cooperative_ids"]):
        category_ids = []
        for category_index, (code, name) in enumerate(category_specs):
            category_id = _uuid(seed, f"category:{coop_index}:{category_index}")
            category_ids.append(category_id)
            categories.append(
                {
                    "id": category_id,
                    "cooperative_id": cooperative_id,
                    "code": code,
                    "name": name,
                    "description": f"{name}虚构演示分类",
                    "is_active": True,
                    "created_at": GENERATED_AT,
                    "updated_at": GENERATED_AT,
                }
            )

        coop_product_ids = []
        for product_index, (code, name, unit, shelf_life, safety, _) in enumerate(
            product_specs
        ):
            product_id = _uuid(seed, f"product:{coop_index}:{product_index}")
            coop_product_ids.append(product_id)
            products.append(
                {
                    "id": product_id,
                    "cooperative_id": cooperative_id,
                    "category_id": category_ids[0 if product_index < 3 else 1],
                    "code": code,
                    "name": name,
                    "unit": unit,
                    "shelf_life_days": shelf_life,
                    "safety_stock": _decimal(safety),
                    "is_active": True,
                    "created_at": GENERATED_AT,
                    "updated_at": GENERATED_AT,
                }
            )
            for batch_index in range(3):
                key = (coop_index, product_index, batch_index)
                batch_id = _uuid(
                    seed, f"batch:{coop_index}:{product_index}:{batch_index}"
                )
                batch_ids[key] = batch_id
                expiry_offset = 8 + product_index * 4 + batch_index * 35
                expiry_date = AS_OF_DATE + timedelta(days=expiry_offset)
                production_date = expiry_date - timedelta(days=shelf_life)
                is_failed = key in failed_batch_keys
                batches.append(
                    {
                        "id": batch_id,
                        "cooperative_id": cooperative_id,
                        "product_id": product_id,
                        "batch_no": (
                            f"SYN-{AS_OF_DATE:%Y%m%d}-{coop_index + 1:02d}-"
                            f"{product_index + 1:02d}-{batch_index + 1:02d}"
                        ),
                        "trace_code": f"TRACE-{_uuid(seed, f'trace:{key}').hex[:20].upper()}",
                        "origin": f"吉林省演示种植基地{coop_index + 1}-{product_index + 1}",
                        "production_date": production_date,
                        "expiry_date": expiry_date,
                        "responsible_person": f"虚构负责人{coop_index + 1}{product_index + 1}",
                        "status": "BLOCKED"
                        if is_failed
                        else ("CREATED" if batch_index == 2 else "IN_STOCK"),
                        "created_by": context["cooperative_admin_ids"][coop_index],
                        "created_at": _at(production_date),
                        "updated_at": GENERATED_AT,
                    }
                )
                inspection_id = _uuid(seed, f"inspection:{key}")
                conclusion = "FAILED" if is_failed else "PASSED"
                inspections.append(
                    {
                        "id": inspection_id,
                        "cooperative_id": cooperative_id,
                        "batch_id": batch_id,
                        "inspection_no": (
                            f"QC-{AS_OF_DATE:%Y%m%d}-{coop_index + 1:02d}-"
                            f"{product_index + 1:02d}-{batch_index + 1:02d}"
                        ),
                        "inspected_at": _at(production_date + timedelta(days=1), 10),
                        "inspector_id": context["staff_ids"][coop_index][
                            batch_index % 2
                        ],
                        "conclusion": conclusion,
                        "remarks": "虚构质检异常，用于预警演示"
                        if is_failed
                        else "各项指标符合演示标准",
                        "created_at": _at(production_date + timedelta(days=1), 10),
                        "updated_at": GENERATED_AT,
                    }
                )
                for item_index, item_name in enumerate(("外观", "水分", "农残快检")):
                    qualified = not is_failed or item_index != 2
                    inspection_items.append(
                        {
                            "id": _uuid(seed, f"inspection-item:{key}:{item_index}"),
                            "inspection_id": inspection_id,
                            "item_name": item_name,
                            "standard_value": "符合演示标准",
                            "result_value": "合格" if qualified else "不合格（虚构）",
                            "is_qualified": qualified,
                            "sort_order": item_index,
                            "created_at": _at(production_date + timedelta(days=1), 10),
                        }
                    )
                if (product_index * 3 + batch_index) % 4 == 0:
                    file_id = _uuid(seed, f"file:{key}")
                    files.append(
                        {
                            "id": file_id,
                            "cooperative_id": cooperative_id,
                            "original_name": f"演示质检报告-{coop_index + 1}-{product_index + 1}-{batch_index + 1}.pdf",
                            "storage_key": f"synthetic/{seed}/{file_id}.pdf",
                            "mime_type": "application/pdf",
                            "size_bytes": rng.randint(80_000, 450_000),
                            "sha256": uuid5(NAMESPACE_URL, str(file_id)).hex * 2,
                            "uploaded_by": context["staff_ids"][coop_index][
                                batch_index % 2
                            ],
                            "created_at": GENERATED_AT,
                        }
                    )
                    inspection_files.append(
                        {
                            "inspection_id": inspection_id,
                            "file_id": file_id,
                            "created_at": GENERATED_AT,
                        }
                    )
        product_ids.append(coop_product_ids)

    tables: list[TableRows] = [
        ("product_categories", categories),
        ("products", products),
        ("batches", batches),
        ("files", files),
        ("quality_inspections", inspections),
        ("quality_inspection_items", inspection_items),
        ("inspection_files", inspection_files),
    ]
    context.update(
        {
            "product_ids": product_ids,
            "product_specs": product_specs,
            "batch_ids": batch_ids,
            "failed_batch_keys": failed_batch_keys,
        }
    )
    return tables, context


def _inventory_rows(
    seed: int, rng: random.Random, context: dict[str, Any]
) -> tuple[list[TableRows], dict[str, Any]]:
    inventories = []
    operations = []
    transactions = []
    trace_events = []
    scope_balances: dict[tuple[int, int, int], Decimal] = {}
    history_start = AS_OF_DATE - timedelta(days=90)

    for coop_index, cooperative_id in enumerate(context["cooperative_ids"]):
        admin_id = context["cooperative_admin_ids"][coop_index]
        for product_index, product_id in enumerate(context["product_ids"][coop_index]):
            _, _, _, _, _, base_demand = context["product_specs"][product_index]
            for warehouse_index, warehouse_id in enumerate(
                context["warehouse_ids"][coop_index]
            ):
                scope = (coop_index, warehouse_index, product_index)
                batch_id = context["batch_ids"][
                    (coop_index, product_index, warehouse_index)
                ]
                daily_quantities: list[Decimal] = []
                for day_index in range(90):
                    current_day = history_start + timedelta(days=day_index)
                    weekend_factor = 1.18 if current_day.weekday() >= 5 else 1.0
                    seasonal = 1 + 0.12 * ((current_day.month % 4) - 1.5)
                    sampled_quantity = max(
                        1.0,
                        rng.gauss(
                            base_demand * weekend_factor * seasonal, base_demand * 0.14
                        ),
                    )
                    daily_quantities.append(_decimal(sampled_quantity))
                final_balance = _decimal(
                    35 + rng.randint(0, 30)
                    if len(scope_balances) < 4
                    else 260 + rng.randint(0, 240)
                )
                inbound_quantity = sum(daily_quantities, final_balance)
                inbound_day = history_start - timedelta(days=7)
                inbound_operation_id = _uuid(seed, f"operation:inbound:{scope}")
                operations.append(
                    {
                        "id": inbound_operation_id,
                        "cooperative_id": cooperative_id,
                        "operation_no": f"IN-SYN-{coop_index + 1}-{warehouse_index + 1}-{product_index + 1}",
                        "operation_type": "INBOUND",
                        "source_warehouse_id": None,
                        "destination_warehouse_id": None,
                        "external_reference": None,
                        "reason": "合成历史期初入库",
                        "occurred_at": _at(inbound_day),
                        "status": "COMPLETED",
                        "created_by": admin_id,
                        "created_at": _at(inbound_day),
                    }
                )
                transactions.append(
                    {
                        "id": _uuid(seed, f"transaction:inbound:{scope}"),
                        "cooperative_id": cooperative_id,
                        "operation_id": inbound_operation_id,
                        "warehouse_id": warehouse_id,
                        "batch_id": batch_id,
                        "transaction_type": "INBOUND",
                        "quantity_delta": inbound_quantity,
                        "quantity_before": _decimal(0),
                        "quantity_after": inbound_quantity,
                        "occurred_at": _at(inbound_day),
                        "created_by": admin_id,
                        "created_at": _at(inbound_day),
                    }
                )
                trace_events.append(
                    {
                        "id": _uuid(seed, f"trace-event:inbound:{scope}"),
                        "cooperative_id": cooperative_id,
                        "batch_id": batch_id,
                        "event_type": "INBOUND",
                        "title": "批次入库",
                        "description": "演示批次完成入库",
                        "event_time": _at(inbound_day),
                        "source_type": "INVENTORY_OPERATION",
                        "source_id": inbound_operation_id,
                        "public_data": {"warehouse": f"演示仓库{warehouse_index + 1}"},
                        "created_by": admin_id,
                        "created_at": _at(inbound_day),
                    }
                )

                balance = inbound_quantity
                for day_index, quantity in enumerate(daily_quantities):
                    current_day = history_start + timedelta(days=day_index)
                    operation_id = _uuid(
                        seed, f"operation:outbound:{scope}:{day_index}"
                    )
                    new_balance = balance - quantity
                    operations.append(
                        {
                            "id": operation_id,
                            "cooperative_id": cooperative_id,
                            "operation_no": (
                                f"OUT-SYN-{coop_index + 1}-{warehouse_index + 1}-"
                                f"{product_index + 1}-{day_index + 1:03d}"
                            ),
                            "operation_type": "OUTBOUND",
                            "source_warehouse_id": None,
                            "destination_warehouse_id": None,
                            "external_reference": None,
                            "reason": "合成日出库记录",
                            "occurred_at": _at(current_day, 15),
                            "status": "COMPLETED",
                            "created_by": context["staff_ids"][coop_index][
                                warehouse_index
                            ],
                            "created_at": _at(current_day, 15),
                        }
                    )
                    transactions.append(
                        {
                            "id": _uuid(
                                seed, f"transaction:outbound:{scope}:{day_index}"
                            ),
                            "cooperative_id": cooperative_id,
                            "operation_id": operation_id,
                            "warehouse_id": warehouse_id,
                            "batch_id": batch_id,
                            "transaction_type": "OUTBOUND",
                            "quantity_delta": -quantity,
                            "quantity_before": balance,
                            "quantity_after": new_balance,
                            "occurred_at": _at(current_day, 15),
                            "created_by": context["staff_ids"][coop_index][
                                warehouse_index
                            ],
                            "created_at": _at(current_day, 15),
                        }
                    )
                    balance = new_balance
                scope_balances[scope] = balance
                inventories.append(
                    {
                        "id": _uuid(seed, f"inventory:{scope}"),
                        "cooperative_id": cooperative_id,
                        "warehouse_id": warehouse_id,
                        "batch_id": batch_id,
                        "quantity": balance,
                        "locked_quantity": _decimal(0),
                        "version": 90,
                        "updated_at": GENERATED_AT,
                    }
                )

    for coop_index, product_index, batch_index in context["batch_ids"]:
        batch_id = context["batch_ids"][(coop_index, product_index, batch_index)]
        cooperative_id = context["cooperative_ids"][coop_index]
        production_date = next(
            row for row in context["catalog_batches"] if row["id"] == batch_id
        )["production_date"]
        trace_events.extend(
            [
                {
                    "id": _uuid(seed, f"trace-event:production:{batch_id}"),
                    "cooperative_id": cooperative_id,
                    "batch_id": batch_id,
                    "event_type": "PRODUCTION",
                    "title": "完成生产",
                    "description": "演示种植基地完成本批次生产",
                    "event_time": _at(production_date, 8),
                    "source_type": "BATCH",
                    "source_id": batch_id,
                    "public_data": {"dataType": "SYNTHETIC"},
                    "created_by": context["cooperative_admin_ids"][coop_index],
                    "created_at": _at(production_date, 8),
                },
                {
                    "id": _uuid(seed, f"trace-event:inspection:{batch_id}"),
                    "cooperative_id": cooperative_id,
                    "batch_id": batch_id,
                    "event_type": "INSPECTION",
                    "title": "完成质量检查",
                    "description": "质量结论见公开追溯记录",
                    "event_time": _at(production_date + timedelta(days=1), 10),
                    "source_type": "QUALITY_INSPECTION",
                    "source_id": _uuid(
                        seed, f"inspection:{(coop_index, product_index, batch_index)}"
                    ),
                    "public_data": {"dataType": "SYNTHETIC"},
                    "created_by": context["staff_ids"][coop_index][batch_index % 2],
                    "created_at": _at(production_date + timedelta(days=1), 10),
                },
            ]
        )

    context["scope_balances"] = scope_balances
    return [
        ("inventories", inventories),
        ("inventory_operations", operations),
        ("inventory_transactions", transactions),
        ("trace_events", trace_events),
    ], context


def _alert_and_ai_rows(
    seed: int, rng: random.Random, context: dict[str, Any]
) -> list[TableRows]:
    alert_rules = []
    alerts = []
    handling_logs = []
    tasks = []
    idempotency_records = []
    models = []
    forecast_results = []
    forecast_points = []
    scopes = list(context["scope_balances"])

    for scope_index, scope in enumerate(scopes):
        coop_index, warehouse_index, product_index = scope
        cooperative_id = context["cooperative_ids"][coop_index]
        warehouse_id = context["warehouse_ids"][coop_index][warehouse_index]
        product_id = context["product_ids"][coop_index][product_index]
        batch_id = context["batch_ids"][(coop_index, product_index, warehouse_index)]
        rule_id = _uuid(seed, f"alert-rule:low-stock:{scope}")
        alert_rules.append(
            {
                "id": rule_id,
                "cooperative_id": cooperative_id,
                "warehouse_id": warehouse_id,
                "product_id": product_id,
                "alert_type": "LOW_STOCK",
                "threshold_quantity": _decimal(
                    context["product_specs"][product_index][4]
                ),
                "threshold_days": None,
                "turnover_days": None,
                "severity": "HIGH",
                "is_enabled": True,
                "created_at": GENERATED_AT,
                "updated_at": GENERATED_AT,
            }
        )
        if scope_index < 4:
            alerts.append(
                {
                    "id": _uuid(seed, f"alert:low-stock:{scope}"),
                    "cooperative_id": cooperative_id,
                    "rule_id": rule_id,
                    "alert_type": "LOW_STOCK",
                    "severity": "HIGH",
                    "status": "PENDING",
                    "warehouse_id": warehouse_id,
                    "product_id": product_id,
                    "batch_id": batch_id,
                    "dedupe_key": f"LOW_STOCK:{warehouse_id}:{product_id}:202609",
                    "title": "安全库存不足（演示）",
                    "message": "当前库存低于演示安全库存阈值，请核对补货计划。",
                    "evidence": {
                        "currentStock": float(context["scope_balances"][scope])
                    },
                    "detected_at": GENERATED_AT - timedelta(hours=scope_index + 1),
                    "resolved_at": None,
                    "assignee_id": context["cooperative_admin_ids"][coop_index],
                    "created_at": GENERATED_AT - timedelta(hours=scope_index + 1),
                    "updated_at": GENERATED_AT,
                }
            )

        train_task_id = _uuid(seed, f"task:train:{scope}")
        forecast_task_id = _uuid(seed, f"task:forecast:{scope}")
        common_task = {
            "cooperative_id": cooperative_id,
            "status": "SUCCESS",
            "progress": 100,
            "error_code": None,
            "error_message": None,
            "requested_by": context["cooperative_admin_ids"][coop_index],
            "started_at": GENERATED_AT - timedelta(minutes=20),
            "finished_at": GENERATED_AT - timedelta(minutes=18),
            "created_at": GENERATED_AT - timedelta(minutes=21),
            "updated_at": GENERATED_AT - timedelta(minutes=18),
        }
        tasks.append(
            {
                "id": train_task_id,
                **common_task,
                "task_type": "MODEL_TRAINING",
                "celery_task_id": f"synthetic-train-{train_task_id}",
                "request_payload": {
                    "warehouseId": str(warehouse_id),
                    "productId": str(product_id),
                    "randomSeed": seed,
                },
                "result_payload": {"dataType": "SYNTHETIC", "status": "completed"},
            }
        )
        tasks.append(
            {
                "id": forecast_task_id,
                **common_task,
                "task_type": "DEMAND_FORECAST",
                "celery_task_id": f"synthetic-forecast-{forecast_task_id}",
                "request_payload": {
                    "warehouseId": str(warehouse_id),
                    "productId": str(product_id),
                    "horizon": "SEVEN_DAYS",
                },
                "result_payload": {"dataType": "SYNTHETIC", "status": "completed"},
            }
        )
        model_id = _uuid(seed, f"model:{scope}")
        model_type = "XGBOOST"
        models.append(
            {
                "id": model_id,
                "cooperative_id": cooperative_id,
                "warehouse_id": warehouse_id,
                "product_id": product_id,
                "task_id": train_task_id,
                "model_type": model_type,
                "version": f"{model_type.lower()}-synthetic-{scope_index + 1:03d}",
                "artifact_path": f"models/synthetic/{model_id}.joblib",
                "data_type": "SYNTHETIC",
                "training_start_date": AS_OF_DATE - timedelta(days=90),
                "training_end_date": AS_OF_DATE - timedelta(days=1),
                "random_seed": seed,
                "parameters": {"nEstimators": 120, "maxDepth": 5},
                "metrics": {
                    "mae": round(8 + rng.random() * 5, 3),
                    "rmse": round(12 + rng.random() * 6, 3),
                },
                "is_active": True,
                "created_by": context["cooperative_admin_ids"][coop_index],
                "created_at": GENERATED_AT - timedelta(minutes=18),
            }
        )
        forecast_id = _uuid(seed, f"forecast:{scope}")
        point_rows = []
        for day_offset in range(7):
            predicted = _decimal(
                context["product_specs"][product_index][5]
                * (
                    1.15
                    if (AS_OF_DATE + timedelta(days=day_offset + 1)).weekday() >= 5
                    else 1
                )
                * rng.uniform(0.9, 1.1)
            )
            point_rows.append((day_offset, predicted))
            forecast_points.append(
                {
                    "id": _uuid(seed, f"forecast-point:{scope}:{day_offset}"),
                    "forecast_result_id": forecast_id,
                    "forecast_date": AS_OF_DATE + timedelta(days=day_offset + 1),
                    "predicted_quantity": predicted,
                    "lower_bound": _decimal(float(predicted) * 0.82),
                    "upper_bound": _decimal(float(predicted) * 1.18),
                }
            )
        predicted_total = sum((quantity for _, quantity in point_rows), _decimal(0))
        current_stock = context["scope_balances"][scope]
        forecast_results.append(
            {
                "id": forecast_id,
                "cooperative_id": cooperative_id,
                "warehouse_id": warehouse_id,
                "product_id": product_id,
                "model_version_id": model_id,
                "task_id": forecast_task_id,
                "horizon_days": 7,
                "forecast_start_date": AS_OF_DATE + timedelta(days=1),
                "forecast_end_date": AS_OF_DATE + timedelta(days=7),
                "predicted_demand": predicted_total,
                "current_stock": current_stock,
                "recommended_replenishment": max(
                    _decimal(0), predicted_total - current_stock
                ),
                "data_type": "SYNTHETIC",
                "metrics": {"mae": 10.25, "rmse": 14.8, "baselineMae": 18.6},
                "important_factors": ["最近7日出库量", "星期", "月份"],
                "limitation_notice": "结果基于合成数据，仅用于验证算法流程，不代表真实经营效果。",
                "generated_at": GENERATED_AT,
            }
        )

    status_specs = [
        ("NEAR_EXPIRY", "MEDIUM", "PROCESSING", 4),
        ("OVERSTOCK", "LOW", "RESOLVED", 2),
    ]
    alert_counter = 4
    for alert_type, severity, status, amount in status_specs:
        for _ in range(amount):
            scope = scopes[alert_counter]
            coop_index, warehouse_index, product_index = scope
            cooperative_id = context["cooperative_ids"][coop_index]
            warehouse_id = context["warehouse_ids"][coop_index][warehouse_index]
            product_id = context["product_ids"][coop_index][product_index]
            batch_id = context["batch_ids"][
                (coop_index, product_index, warehouse_index)
            ]
            alert_id = _uuid(seed, f"alert:{alert_type}:{scope}")
            resolved_at = (
                GENERATED_AT - timedelta(hours=1) if status == "RESOLVED" else None
            )
            alerts.append(
                {
                    "id": alert_id,
                    "cooperative_id": cooperative_id,
                    "rule_id": None,
                    "alert_type": alert_type,
                    "severity": severity,
                    "status": status,
                    "warehouse_id": warehouse_id,
                    "product_id": product_id,
                    "batch_id": batch_id,
                    "dedupe_key": f"{alert_type}:{warehouse_id}:{batch_id}:202609",
                    "title": f"{alert_type}演示预警",
                    "message": "由合成数据生成的演示预警。",
                    "evidence": {"dataType": "SYNTHETIC"},
                    "detected_at": GENERATED_AT - timedelta(days=2),
                    "resolved_at": resolved_at,
                    "assignee_id": context["cooperative_admin_ids"][coop_index],
                    "created_at": GENERATED_AT - timedelta(days=2),
                    "updated_at": GENERATED_AT,
                }
            )
            handling_logs.append(
                {
                    "id": _uuid(seed, f"alert-log:{alert_id}"),
                    "alert_id": alert_id,
                    "operator_id": context["cooperative_admin_ids"][coop_index],
                    "from_status": "PENDING",
                    "to_status": status,
                    "comment": "演示处理记录",
                    "created_at": resolved_at or GENERATED_AT - timedelta(days=1),
                }
            )
            alert_counter += 1

    for failed_key in sorted(context["failed_batch_keys"]):
        coop_index, product_index, _ = failed_key
        cooperative_id = context["cooperative_ids"][coop_index]
        product_id = context["product_ids"][coop_index][product_index]
        batch_id = context["batch_ids"][failed_key]
        alerts.append(
            {
                "id": _uuid(seed, f"alert:quality:{failed_key}"),
                "cooperative_id": cooperative_id,
                "rule_id": None,
                "alert_type": "QUALITY_FAILED",
                "severity": "CRITICAL",
                "status": "PENDING",
                "warehouse_id": None,
                "product_id": product_id,
                "batch_id": batch_id,
                "dedupe_key": f"QUALITY_FAILED:{batch_id}",
                "title": "质检异常（演示）",
                "message": "虚构批次农残快检项目不合格，已锁定批次。",
                "evidence": {"dataType": "SYNTHETIC", "item": "农残快检"},
                "detected_at": GENERATED_AT - timedelta(days=1),
                "resolved_at": None,
                "assignee_id": context["cooperative_admin_ids"][coop_index],
                "created_at": GENERATED_AT - timedelta(days=1),
                "updated_at": GENERATED_AT,
            }
        )

    for index, scope in enumerate(scopes[:8]):
        coop_index, _, _ = scope
        user_id = context["staff_ids"][coop_index][index % 2]
        idempotency_records.append(
            {
                "id": _uuid(seed, f"idempotency:{index}"),
                "cooperative_id": context["cooperative_ids"][coop_index],
                "user_id": user_id,
                "endpoint": "/api/v1/inventory-issues",
                "idempotency_key": f"synthetic-request-{seed}-{index + 1}",
                "request_hash": uuid5(NAMESPACE_URL, f"request:{seed}:{index}").hex * 2,
                "status": "COMPLETED",
                "response_status": 201,
                "response_body": {"dataType": "SYNTHETIC", "accepted": True},
                "expires_at": GENERATED_AT + timedelta(days=1),
                "created_at": GENERATED_AT,
                "updated_at": GENERATED_AT,
            }
        )

    audit_logs = []
    auditable_users = [
        _uuid(seed, "user:sysadmin"),
        *context["cooperative_admin_ids"],
        *(staff for coop_staff in context["staff_ids"] for staff in coop_staff),
    ]
    for index in range(20):
        user_id = auditable_users[index % len(auditable_users)]
        audit_logs.append(
            {
                "id": _uuid(seed, f"audit:{index}"),
                "cooperative_id": context["user_cooperative_ids"][user_id],
                "user_id": user_id,
                "action": ("LOGIN" if index % 4 == 0 else "READ"),
                "module": ("identity" if index % 4 == 0 else "inventory"),
                "object_type": ("SESSION" if index % 4 == 0 else "INVENTORY"),
                "object_id": None,
                "result": "SUCCESS",
                "request_id": f"synthetic-{seed}-{index + 1:04d}",
                "ip_address": f"192.0.2.{index + 1}",
                "user_agent": "Synthetic-Demo-Client/1.0",
                "detail": {"dataType": "SYNTHETIC"},
                "created_at": GENERATED_AT - timedelta(minutes=index * 5),
            }
        )

    return [
        ("alert_rules", alert_rules),
        ("alerts", alerts),
        ("alert_handling_logs", handling_logs),
        ("task_records", tasks),
        ("idempotency_records", idempotency_records),
        ("model_versions", models),
        ("forecast_results", forecast_results),
        ("forecast_points", forecast_points),
        ("audit_logs", audit_logs),
    ]


def generate_demo_sql(seed: int = DEFAULT_SEED) -> str:
    """返回使用固定随机种子生成的完整演示数据SQL。"""
    rng = random.Random(seed)
    fake = Faker("zh_CN")
    fake.seed_instance(seed)

    base_tables, context = _base_rows(seed, rng, fake)
    catalog_tables, context = _catalog_rows(seed, rng, context)
    context["catalog_batches"] = next(
        rows for table, rows in catalog_tables if table == "batches"
    )
    inventory_tables, context = _inventory_rows(seed, rng, context)
    final_tables = _alert_and_ai_rows(seed, rng, context)
    all_tables = [*base_tables, *catalog_tables, *inventory_tables, *final_tables]

    lines = [
        "-- 农产品批次追溯与智能库存预警系统演示数据",
        "-- 全部为虚构合成数据（SYNTHETIC），仅用于毕业设计展示与测试。",
        "-- 不代表任何真实合作社、人员、库存、质检或经营情况。",
        f"-- RANDOM_SEED: {seed}",
        f"-- GENERATED_AS_OF: {GENERATED_AT.isoformat(timespec='seconds')}",
        "-- 可重复执行：所有INSERT均使用ON CONFLICT DO NOTHING。",
        "",
    ]
    lines.extend(f"-- ROW_COUNT {table}: {len(rows)}" for table, rows in all_tables)
    lines.extend(["", "BEGIN;", ""])
    lines.extend(
        _render_insert(table, rows) + "\n" for table, rows in all_tables if rows
    )
    lines.extend(["COMMIT;", ""])
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成可复现的虚构演示数据SQL")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="随机种子")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("sql/demo_data.sql"),
        help="输出SQL文件路径",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    output: Path = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate_demo_sql(args.seed), encoding="utf-8", newline="\n")
    print(f"已生成虚构演示数据：{output}（随机种子={args.seed}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
