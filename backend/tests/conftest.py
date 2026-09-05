from __future__ import annotations

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from app.models import Base
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from tests.support import skip_or_fail


def _database_url_from_environment() -> str | None:
    return os.getenv("TEST_POSTGRES_DATABASE_URL") or os.getenv("TEST_DATABASE_URL")


def _asyncpg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture
def postgres_database_url() -> str:
    url = _database_url_from_environment()
    if not url:
        skip_or_fail(
            "postgres",
            "未配置 TEST_POSTGRES_DATABASE_URL 或 TEST_DATABASE_URL，无法执行 PostgreSQL 门禁测试",
        )
    return _asyncpg_url(url)


@pytest_asyncio.fixture
async def postgres_schema(postgres_database_url: str) -> AsyncIterator[str]:
    """为每个测试建立并清理独立 PostgreSQL schema。"""
    schema_name = f"test_{uuid4().hex}"
    admin_engine = create_async_engine(postgres_database_url, poolclass=NullPool)
    quoted_schema = f'"{schema_name}"'
    schema_created = False
    try:
        async with admin_engine.begin() as connection:
            await connection.execute(text(f"CREATE SCHEMA {quoted_schema}"))
        schema_created = True
        yield schema_name
    finally:
        if schema_created:
            async with admin_engine.begin() as connection:
                await connection.execute(text(f"DROP SCHEMA {quoted_schema} CASCADE"))
        await admin_engine.dispose()


@pytest_asyncio.fixture
async def postgres_engine(
    postgres_database_url: str,
    postgres_schema: str,
) -> AsyncIterator[AsyncEngine]:
    """提供使用独立 schema 的 PostgreSQL 测试引擎。"""
    engine = create_async_engine(
        postgres_database_url,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": postgres_schema}},
    )
    try:

        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
        except SQLAlchemyError as error:
            skip_or_fail("postgres", f"PostgreSQL 测试数据库不可用：{error}")

        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def postgres_session_factory(
    postgres_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        postgres_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture
async def postgres_session(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with postgres_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
