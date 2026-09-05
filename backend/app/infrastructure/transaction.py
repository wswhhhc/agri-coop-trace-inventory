from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transaction_scope(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    """为一个业务用例建立显式事务边界。

    正常退出时提交事务，业务异常或数据库异常时由 SQLAlchemy 自动回滚。
    事务边界应由 Service 层建立，Repository 不应自行提交事务。
    """
    async with session.begin():
        yield session


__all__ = ["transaction_scope"]
