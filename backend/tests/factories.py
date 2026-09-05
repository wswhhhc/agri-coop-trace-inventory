from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from itertools import count
from typing import Any

from app.models import (
    Batch,
    BatchStatus,
    Cooperative,
    Permission,
    Product,
    ProductCategory,
    Role,
    User,
    UserStatus,
    UserWarehouse,
    Warehouse,
)

_sequence = count(1)


def _next_code(prefix: str) -> str:
    return f"{prefix}-{next(_sequence)}"


def cooperative_factory(**overrides: Any) -> Cooperative:
    values = {
        "code": _next_code("coop"),
        "name": "测试合作社",
    }
    values.update(overrides)
    return Cooperative(**values)


def role_factory(**overrides: Any) -> Role:
    values = {
        "code": _next_code("ROLE").upper(),
        "name": "测试角色",
    }
    values.update(overrides)
    return Role(**values)


def permission_factory(**overrides: Any) -> Permission:
    values = {
        "code": _next_code("test:permission"),
        "name": "测试权限",
        "module": "test",
    }
    values.update(overrides)
    return Permission(**values)


def user_factory(
    *,
    cooperative: Cooperative | None = None,
    role: Role | None = None,
    **overrides: Any,
) -> User:
    values = {
        "cooperative": cooperative or cooperative_factory(),
        "role": role or role_factory(),
        "username": _next_code("user").lower(),
        "password_hash": "test-password-hash",
        "real_name": "测试用户",
        "status": UserStatus.ACTIVE,
    }
    values.update(overrides)
    return User(**values)


def warehouse_factory(
    *,
    cooperative: Cooperative | None = None,
    **overrides: Any,
) -> Warehouse:
    values = {
        "cooperative": cooperative or cooperative_factory(),
        "code": _next_code("warehouse"),
        "name": "测试仓库",
    }
    values.update(overrides)
    return Warehouse(**values)


def product_category_factory(
    *,
    cooperative: Cooperative | None = None,
    **overrides: Any,
) -> ProductCategory:
    values = {
        "cooperative": cooperative or cooperative_factory(),
        "code": _next_code("category"),
        "name": _next_code("分类"),
    }
    values.update(overrides)
    return ProductCategory(**values)


def product_factory(
    *,
    cooperative: Cooperative | None = None,
    category: ProductCategory | None = None,
    **overrides: Any,
) -> Product:
    category = category or product_category_factory(cooperative=cooperative)
    values = {
        "cooperative": cooperative or category.cooperative,
        "category": category,
        "code": _next_code("product"),
        "name": "测试农产品",
        "unit": "kg",
        "shelf_life_days": 7,
        "safety_stock": Decimal("10.000"),
    }
    values.update(overrides)
    return Product(**values)


def batch_factory(
    *,
    cooperative: Cooperative | None = None,
    product: Product | None = None,
    creator: User | None = None,
    **overrides: Any,
) -> Batch:
    product = product or product_factory(cooperative=cooperative)
    cooperative = cooperative or product.cooperative
    creator = creator or user_factory(cooperative=cooperative)
    production_date = date(2026, 9, 5)
    values = {
        "cooperative": cooperative,
        "product": product,
        "creator": creator,
        "batch_no": _next_code("batch"),
        "trace_code": _next_code("trace"),
        "origin": "测试种植基地",
        "production_date": production_date,
        "expiry_date": production_date + timedelta(days=7),
        "status": BatchStatus.CREATED,
    }
    values.update(overrides)
    return Batch(**values)


def user_warehouse_factory(
    *,
    user: User | None = None,
    warehouse: Warehouse | None = None,
    **overrides: Any,
) -> UserWarehouse:
    values = {
        "user": user or user_factory(),
        "warehouse": warehouse or warehouse_factory(),
    }
    values.update(overrides)
    return UserWarehouse(**values)


__all__ = [
    "batch_factory",
    "cooperative_factory",
    "permission_factory",
    "product_category_factory",
    "product_factory",
    "role_factory",
    "user_factory",
    "user_warehouse_factory",
    "warehouse_factory",
]
