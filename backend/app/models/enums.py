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


class InspectionConclusion(StrEnum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class SortDirection(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


class InventoryOperationType(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    ADJUSTMENT = "ADJUSTMENT"
    DAMAGE = "DAMAGE"
    TRANSFER = "TRANSFER"


class InventoryOperationStatus(StrEnum):
    COMPLETED = "COMPLETED"
    REVERSED = "REVERSED"


class InventoryTransactionType(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    ADJUSTMENT = "ADJUSTMENT"
    DAMAGE = "DAMAGE"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"


class InventoryRisk(StrEnum):
    NORMAL = "NORMAL"
    LOW_STOCK = "LOW_STOCK"
    NEAR_EXPIRY = "NEAR_EXPIRY"
    OVERSTOCK = "OVERSTOCK"


class IdempotencyStatus(StrEnum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


__all__ = [
    "BatchStatus",
    "CooperativeStatus",
    "IdempotencyStatus",
    "InspectionConclusion",
    "InventoryOperationStatus",
    "InventoryOperationType",
    "InventoryRisk",
    "InventoryTransactionType",
    "SortDirection",
    "UserStatus",
    "WarehouseStatus",
    "enum_sql_values",
]
