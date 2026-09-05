from enum import StrEnum


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
]
