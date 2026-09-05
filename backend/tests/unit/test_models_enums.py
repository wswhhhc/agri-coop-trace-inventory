from app.models import Cooperative, User, Warehouse
from app.models.enums import (
    BatchStatus,
    CooperativeStatus,
    SortDirection,
    UserStatus,
    WarehouseStatus,
)
from app.schemas.common import SortOrder
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import inspect


def test_domain_enums_have_the_documented_values() -> None:
    assert [item.value for item in UserStatus] == ["ACTIVE", "LOCKED", "INACTIVE"]
    assert [item.value for item in CooperativeStatus] == ["ACTIVE", "INACTIVE"]
    assert [item.value for item in WarehouseStatus] == ["ACTIVE", "INACTIVE"]
    assert [item.value for item in BatchStatus] == [
        "CREATED",
        "IN_STOCK",
        "DEPLETED",
        "BLOCKED",
        "EXPIRED",
    ]


def test_api_sort_order_reuses_the_domain_sort_direction() -> None:
    assert SortOrder is SortDirection
    assert SortOrder.ASC.value == "ASC"
    assert SortOrder.DESC.value == "DESC"


def test_status_columns_use_the_shared_enum_types() -> None:
    assert isinstance(inspect(User).columns.status.type, SqlEnum)
    assert inspect(User).columns.status.type.enum_class is UserStatus
    assert inspect(Cooperative).columns.status.type.enum_class is CooperativeStatus
    assert inspect(Warehouse).columns.status.type.enum_class is WarehouseStatus
