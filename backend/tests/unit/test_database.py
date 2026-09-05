from __future__ import annotations

from typing import Self

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.infrastructure import database


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "jwt_secret_key": "unit-test-secret",
        "postgres_password": "unit-test-password",
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.asyncio
async def test_create_database_engine_uses_async_postgres_and_pool_settings() -> None:
    settings = _settings(
        db_pool_size=4,
        db_max_overflow=6,
        db_pool_timeout_seconds=12,
        db_pool_recycle_seconds=300,
        db_echo=True,
    )

    engine = database.create_database_engine(settings)
    try:
        assert engine.url.drivername == "postgresql+asyncpg"
        assert engine.url.database == "agri_trace"
        assert engine.echo is True
        assert engine.pool.size() == 4
        assert engine.pool._max_overflow == 6
        assert engine.pool._timeout == 12
        assert engine.pool._recycle == 300
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_create_session_factory_creates_non_expiring_async_sessions() -> None:
    settings = _settings()
    engine = database.create_database_engine(settings)
    try:
        session_factory = database.create_session_factory(engine)
        session = session_factory()

        assert isinstance(session, AsyncSession)
        assert session.sync_session.expire_on_commit is False
        assert session.sync_session.autoflush is False
        await session.close()
    finally:
        await engine.dispose()


class _FakeSession:
    def __init__(self) -> None:
        self.rollback_called = False
        self.closed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        self.closed = True

    async def rollback(self) -> None:
        self.rollback_called = True


class _FakeSessionFactory:
    def __init__(self) -> None:
        self.session = _FakeSession()

    def __call__(self) -> _FakeSession:
        return self.session


@pytest.mark.asyncio
async def test_get_db_session_rolls_back_on_request_error(monkeypatch) -> None:
    session_factory = _FakeSessionFactory()
    monkeypatch.setattr(database, "SessionLocal", session_factory)

    session_generator = database.get_db_session()
    session = await anext(session_generator)

    assert session is session_factory.session

    with pytest.raises(RuntimeError, match="request failed"):
        await session_generator.athrow(RuntimeError("request failed"))

    assert session_factory.session.rollback_called is True
    assert session_factory.session.closed is True


@pytest.mark.asyncio
async def test_dispose_database_engine_closes_engine(monkeypatch) -> None:
    class _FakeEngine:
        disposed = False

        async def dispose(self) -> None:
            self.disposed = True

    fake_engine = _FakeEngine()
    monkeypatch.setattr(database, "engine", fake_engine)

    await database.dispose_database_engine()

    assert fake_engine.disposed is True
