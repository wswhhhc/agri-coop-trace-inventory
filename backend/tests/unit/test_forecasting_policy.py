from uuid import uuid4

import pytest
from app.core.auth.authorization import permission_denied, resource_not_found
from app.core.auth.context import AuthContext
from app.services.forecasting_policy import (
    require_model_manage,
    require_model_read,
    warehouse_ids_for_query,
)


def _context(role: str, permissions: set[str], warehouse_ids=None) -> AuthContext:
    return AuthContext(
        uuid4(),
        "u",
        "用户",
        role,
        frozenset(permissions),
        uuid4(),
        warehouse_ids,
        "s",
        "t",
    )


def test_model_permissions_match_roles_and_codes() -> None:
    admin = _context("COOPERATIVE_ADMIN", {"model:read", "model:manage"})
    staff = _context("WAREHOUSE_STAFF", {"model:read"}, frozenset({uuid4()}))
    with pytest.raises(type(permission_denied())):
        require_model_manage(staff)
    require_model_manage(admin)
    require_model_read(staff)
    assert warehouse_ids_for_query(staff) == staff.warehouse_ids
    assert warehouse_ids_for_query(admin) is None


def test_model_policy_raises_uniform_application_errors() -> None:
    with pytest.raises(type(resource_not_found())):
        raise resource_not_found()
