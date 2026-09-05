from __future__ import annotations

from types import SimpleNamespace
from typing import Self, cast
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from app.core.auth.flows import AuthenticationService
from app.core.auth.service import AuthService
from app.core.config import Settings
from app.core.exceptions import AppException
from app.infrastructure import database
from app.infrastructure.transaction import transaction_scope
from app.models import SYSTEM_ADMIN_ROLE_CODE
from sqlalchemy.ext.asyncio import AsyncSession


class _FakeTransaction:
    def __init__(self) -> None:
        self.entered = False
        self.exited = False
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> Self:
        self.entered = True
        return self

    async def __aexit__(self, exc_type: object, *_args: object) -> None:
        self.exited = True
        if exc_type is None:
            self.committed = True
        else:
            self.rolled_back = True


class _FakeSession:
    def __init__(self) -> None:
        self.transaction = _FakeTransaction()
        self.closed = False

    def begin(self) -> _FakeTransaction:
        return self.transaction

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        self.closed = True


class _FakeSessionFactory:
    def __init__(self) -> None:
        self.session = _FakeSession()

    def __call__(self) -> _FakeSession:
        return self.session


@pytest.mark.asyncio
async def test_transaction_scope_commits_when_context_exits_normally() -> None:
    session = _FakeSession()

    async with transaction_scope(cast(AsyncSession, session)):
        assert session.transaction.entered is True

    assert session.transaction.exited is True
    assert session.transaction.committed is True
    assert session.transaction.rolled_back is False


@pytest.mark.asyncio
async def test_transaction_scope_rolls_back_and_propagates_error() -> None:
    session = _FakeSession()

    with pytest.raises(RuntimeError, match="write failed"):
        async with transaction_scope(cast(AsyncSession, session)):
            raise RuntimeError("write failed")

    assert session.transaction.exited is True
    assert session.transaction.committed is False
    assert session.transaction.rolled_back is True


@pytest.mark.asyncio
async def test_get_transactional_session_commits_and_closes_session(
    monkeypatch,
) -> None:
    session_factory = _FakeSessionFactory()
    monkeypatch.setattr(database, "SessionLocal", session_factory)

    session_generator = database.get_transactional_session()
    session = await anext(session_generator)
    assert session is session_factory.session

    with pytest.raises(StopAsyncIteration):
        await anext(session_generator)

    assert session_factory.session.transaction.committed is True
    assert session_factory.session.closed is True


@pytest.mark.asyncio
async def test_get_transactional_session_rolls_back_on_request_error(
    monkeypatch,
) -> None:
    session_factory = _FakeSessionFactory()
    monkeypatch.setattr(database, "SessionLocal", session_factory)

    session_generator = database.get_transactional_session()
    await anext(session_generator)

    with pytest.raises(RuntimeError, match="request failed"):
        await session_generator.athrow(RuntimeError("request failed"))

    assert session_factory.session.transaction.committed is False
    assert session_factory.session.transaction.rolled_back is True
    assert session_factory.session.closed is True


@pytest.mark.asyncio
async def test_get_transactional_session_rolls_back_when_dependency_is_closed(
    monkeypatch,
) -> None:
    session_factory = _FakeSessionFactory()
    monkeypatch.setattr(database, "SessionLocal", session_factory)

    session_generator = database.get_transactional_session()
    await anext(session_generator)
    await session_generator.aclose()

    assert session_factory.session.transaction.committed is False
    assert session_factory.session.transaction.rolled_back is True
    assert session_factory.session.closed is True


@pytest.mark.asyncio
async def test_get_transactional_session_requires_initialized_database(
    monkeypatch,
) -> None:
    monkeypatch.setattr(database, "SessionLocal", None)

    with pytest.raises(RuntimeError, match="数据库尚未初始化"):
        await anext(database.get_transactional_session())


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        postgres_password="unit-test-password",
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
    )


@pytest.mark.asyncio
async def test_authentication_service_owns_login_transaction() -> None:
    session = _FakeSession()
    service = AuthenticationService(
        cast(AsyncSession, session), _settings(), cast(object, object())
    )
    service.user_repository.get_by_username_with_access = AsyncMock(
        return_value=None
    )

    with pytest.raises(AppException, match="用户名或密码错误"):
        await service.login("unknown", "wrong-password")

    assert session.transaction.entered is True
    assert session.transaction.rolled_back is True


@pytest.mark.asyncio
async def test_auth_service_owns_context_transaction() -> None:
    session = _FakeSession()
    service = AuthService(cast(AsyncSession, session), _settings())
    user_id = UUID("11111111-1111-4111-8111-111111111111")
    service._decode_token = lambda _token: {
        "sub": str(user_id),
        "sid": "session-1",
        "jti": "token-1",
    }
    service.user_repository.get_by_id_with_access = AsyncMock(
        return_value=SimpleNamespace(
            id=user_id,
            username="admin",
            real_name="管理员",
            status="ACTIVE",
            cooperative_id=None,
            cooperative=None,
            role=SimpleNamespace(code=SYSTEM_ADMIN_ROLE_CODE, permissions=[]),
        )
    )

    context = await service.build_context("token")

    assert context.user_id == user_id
    assert session.transaction.entered is True
    assert session.transaction.committed is True
