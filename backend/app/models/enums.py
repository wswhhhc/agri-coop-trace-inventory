from enum import StrEnum


def enum_sql_values(enum_type: type[StrEnum]) -> str:
    """返回供 CHECK 约束使用的静态枚举值列表。"""
    return ", ".join(f"'{item.value}'" for item in enum_type)


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    INACTIVE = "INACTIVE"


class CooperativeStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class WarehouseStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class BatchStatus(StrEnum):
    CREATED = "CREATED"
    IN_STOCK = "IN_STOCK"
    DEPLETED = "DEPLETED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"


class SortDirection(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


__all__ = [
    "BatchStatus",
    "CooperativeStatus",
    "SortDirection",
    "UserStatus",
    "WarehouseStatus",
    "enum_sql_values",
]
