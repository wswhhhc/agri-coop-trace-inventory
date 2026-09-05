from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import DatabaseSettings

SessionFactory = async_sessionmaker[AsyncSession]

engine: AsyncEngine | None = None
SessionLocal: SessionFactory | None = None


def create_database_engine(settings: DatabaseSettings) -> AsyncEngine:
    """根据配置创建异步 PostgreSQL 引擎，不在此处建立网络连接。"""
    return create_async_engine(
        settings.sqlalchemy_database_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
        pool_recycle=settings.db_pool_recycle_seconds,
    )


def create_session_factory(database_engine: AsyncEngine) -> SessionFactory:
    """创建请求间隔离的异步会话工厂。"""
    return async_sessionmaker(
        bind=database_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def initialize_database(settings: DatabaseSettings) -> AsyncEngine:
    """初始化进程级引擎和会话工厂。"""
    global SessionLocal, engine

    if engine is None:
        engine = create_database_engine(settings)
        SessionLocal = create_session_factory(engine)
    return engine


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """提供一个请求级会话；异常时回滚，正常结束不自动提交。"""
    if SessionLocal is None:
        raise RuntimeError("数据库尚未初始化")

    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_database_engine() -> None:
    """释放进程级连接池，供应用关闭生命周期调用。"""
    global SessionLocal, engine

    if engine is not None:
        await engine.dispose()
    engine = None
    SessionLocal = None


__all__ = [
    "SessionLocal",
    "create_database_engine",
    "create_session_factory",
    "dispose_database_engine",
    "engine",
    "get_db_session",
    "initialize_database",
]
