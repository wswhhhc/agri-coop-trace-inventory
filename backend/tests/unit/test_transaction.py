from __future__ import annotations

from typing import Self, cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure import database
from app.infrastructure.transaction import transaction_scope


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
