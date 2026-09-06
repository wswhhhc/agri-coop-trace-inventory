from __future__ import annotations

from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IdempotencyRecord, IdempotencyStatus


class IdempotencyRecordRepository:
    """幂等请求记录仓储；通过数据库唯一键原子占用请求。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def claim(
        self,
        *,
        cooperative_id: UUID,
        user_id: UUID,
        endpoint: str,
        idempotency_key: str,
        request_hash: str,
        expires_at: datetime,
    ) -> tuple[IdempotencyRecord, bool]:
        statement = (
            insert(IdempotencyRecord)
            .values(
                cooperative_id=cooperative_id,
                user_id=user_id,
                endpoint=endpoint,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                status=IdempotencyStatus.PROCESSING,
                expires_at=expires_at,
            )
            .on_conflict_do_nothing(
                index_elements=["user_id", "endpoint", "idempotency_key"]
            )
        )
        result = cast(CursorResult[Any], await self.session.execute(statement))
        record = await self.session.scalar(
            select(IdempotencyRecord)
            .where(IdempotencyRecord.user_id == user_id)
            .where(IdempotencyRecord.endpoint == endpoint)
            .where(IdempotencyRecord.idempotency_key == idempotency_key)
            .with_for_update()
        )
        if record is None:
            raise RuntimeError("幂等记录占用失败")
        return record, result.rowcount == 1

    async def complete(
        self,
        record: IdempotencyRecord,
        *,
        response_status: int,
        response_body: dict[str, object],
    ) -> IdempotencyRecord:
        record.status = IdempotencyStatus.COMPLETED
        record.response_status = response_status
        record.response_body = response_body
        await self.session.flush()
        return record


__all__ = ["IdempotencyRecordRepository"]
