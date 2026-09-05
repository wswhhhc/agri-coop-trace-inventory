from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from app.core.auth.context import AuthContext
from app.core.auth.dependencies import _extract_bearer_token, get_auth_context
from app.core.auth.service import AuthService
from app.core.exceptions import AppException
from app.core.security import create_access_token
from app.models import Cooperative, Permission, Role, User, UserWarehouse, Warehouse
from app.models.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.requests import Request

SECRET_KEY = "unit-test-secret-with-at-least-32-bytes"


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        jwt_secret_key=SimpleNamespace(get_secret_value=lambda: SECRET_KEY),
        jwt_algorithm="HS256",
        jwt_issuer=None,
        jwt_audience=None,
    )


def _token(user_id: UUID, *, role: str = "COOPERATIVE_ADMIN") -> str:
    return create_access_token(
        subject=str(user_id),
        session_id="session-1",
        role=role,
        cooperative_id=None,
        secret_key=SECRET_KEY,
    )


@pytest_asyncio.fixture
async def auth_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    uuid_defaults = []
    for table in Base.metadata.tables.values():
        id_column = table.c.get("id")
        if id_column is not None and id_column.server_default is not None:
            uuid_defaults.append((id_column, id_column.server_default))
            id_column.server_default = None

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    for column, server_default in uuid_defaults:
        column.server_default = server_default

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


def _request(authorization: str | None) -> Request:
    headers = (
        [] if authorization is None else [(b"authorization", authorization.encode())]
    )
    return Request({"type": "http", "headers": headers})


class _RevokedSessionStore:
    async def get(self, _session_id: str):
        return None


@pytest.mark.asyncio
async def test_auth_service_builds_context_from_current_database_access(
    auth_session: AsyncSession,
) -> None:
    cooperative = Cooperative(code="coop-1", name="第一合作社")
    role = Role(code="WAREHOUSE_STAFF", name="仓库人员")
    role.permissions.append(
        Permission(code="inventory:read", name="查看库存", module="inventory")
    )
    user = User(
        cooperative=cooperative,
        role=role,
        username="staff",
        password_hash="hashed",
        real_name="仓库人员",
    )
    warehouse = Warehouse(cooperative=cooperative, code="main", name="中心仓")
    user.user_warehouses.append(UserWarehouse(warehouse=warehouse))
    auth_session.add(user)
    await auth_session.commit()

    context = await AuthService(auth_session, _settings()).build_context(
        _token(user.id, role="SYSTEM_ADMIN")
    )

    assert context == AuthContext(
        user_id=user.id,
        username="staff",
        real_name="仓库人员",
        role_code="WAREHOUSE_STAFF",
        permission_codes=frozenset({"inventory:read"}),
        cooperative_id=cooperative.id,
        warehouse_ids=frozenset({warehouse.id}),
        session_id="session-1",
        token_id=context.token_id,
    )
    assert context.has_permission("inventory:read") is True
    assert context.has_warehouse_access(warehouse.id) is True


@pytest.mark.asyncio
async def test_cooperative_admin_context_contains_all_active_warehouses(
    auth_session: AsyncSession,
) -> None:
    cooperative = Cooperative(code="coop-1", name="第一合作社")
    role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
    user = User(
        cooperative=cooperative,
        role=role,
        username="admin",
        password_hash="hashed",
        real_name="管理员",
    )
    active = Warehouse(cooperative=cooperative, code="active", name="有效仓")
    inactive = Warehouse(
        cooperative=cooperative, code="inactive", name="停用仓", status="INACTIVE"
    )
    auth_session.add_all([user, active, inactive])
    await auth_session.commit()

    context = await AuthService(auth_session, _settings()).build_context(
        _token(user.id)
    )

    assert context.warehouse_ids == frozenset({active.id})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token_factory",
    [
        lambda user_id: "not-a-jwt",
        lambda user_id: _token(uuid4()),
    ],
)
async def test_auth_service_returns_401_for_invalid_or_missing_user(
    auth_session: AsyncSession,
    token_factory,
) -> None:
    with pytest.raises(AppException) as error:
        await AuthService(auth_session, _settings()).build_context(
            token_factory(uuid4())
        )

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_service_returns_401_for_disabled_user(
    auth_session: AsyncSession,
) -> None:
    role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
    user = User(
        role=role,
        username="disabled",
        password_hash="hashed",
        real_name="禁用用户",
        status="INACTIVE",
    )
    auth_session.add(user)
    await auth_session.commit()

    with pytest.raises(AppException) as error:
        await AuthService(auth_session, _settings()).build_context(_token(user.id))

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_service_returns_401_for_expired_token(
    auth_session: AsyncSession,
) -> None:
    expired_token = create_access_token(
        subject=str(uuid4()),
        session_id="session-1",
        role="COOPERATIVE_ADMIN",
        cooperative_id=None,
        secret_key=SECRET_KEY,
        now=datetime.now(UTC) - timedelta(minutes=2),
        expires_minutes=1,
    )

    with pytest.raises(AppException) as error:
        await AuthService(auth_session, _settings()).build_context(expired_token)

    assert error.value.status_code == 401
    assert error.value.code == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_auth_service_rejects_access_token_when_redis_session_is_revoked(
    auth_session: AsyncSession,
) -> None:
    role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
    cooperative = Cooperative(code="coop-revoked", name="合作社")
    user = User(
        cooperative=cooperative,
        role=role,
        username="revoked_session",
        password_hash="hashed",
        real_name="会话用户",
    )
    auth_session.add(user)
    await auth_session.commit()

    with pytest.raises(AppException) as error:
        await AuthService(
            auth_session,
            _settings(),
            _RevokedSessionStore(),
        ).build_context(_token(user.id))

    assert error.value.status_code == 401
    assert error.value.code == "AUTHENTICATION_REQUIRED"


@pytest.mark.asyncio
async def test_dependency_returns_401_when_authorization_header_is_missing(
    auth_session: AsyncSession,
) -> None:
    with pytest.raises(AppException) as error:
        await get_auth_context(_request(None), auth_session, _settings())

    assert error.value.status_code == 401


def test_dependency_extracts_bearer_token_from_authorization_header() -> None:
    assert _extract_bearer_token("Bearer token-value") == "token-value"


@pytest.mark.parametrize("authorization", ["Basic token-value", "Bearer", "Bearer "])
def test_dependency_returns_401_for_malformed_authorization_header(
    authorization: str,
) -> None:
    with pytest.raises(AppException) as error:
        _extract_bearer_token(authorization)

    assert error.value.status_code == 401
