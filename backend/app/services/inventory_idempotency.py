from __future__ import annotations

import json
from datetime import timedelta
from typing import cast
from uuid import UUID

from fastapi.encoders import jsonable_encoder

from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.models import IdempotencyStatus
from app.models._common import utc_now
from app.repositories.idempotency_record import IdempotencyRecordRepository
from app.schemas.common import BaseSchema
from app.utils.crypto import sha256_hex


class InventoryIdempotency:
    """库存写操作的幂等键占用、响应回放和完成记录。"""

    def __init__(self, repository: IdempotencyRecordRepository) -> None:
        self.repository = repository

    async def prepare(
        self,
        context: AuthContext,
        cooperative_id: UUID,
        endpoint: str,
        idempotency_key: str,
        payload: BaseSchema,
    ) -> dict[str, object] | None:
        request_hash = request_hash_for(payload)
        record, created = await self.repository.claim(
            cooperative_id=cooperative_id,
            user_id=context.user_id,
            endpoint=endpoint,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            expires_at=utc_now() + timedelta(days=7),
        )
        if created:
            return None
        if record.request_hash != request_hash:
            raise AppException(
                code="IDEMPOTENCY_PAYLOAD_MISMATCH",
                message="相同幂等键对应的请求内容不同",
                status_code=422,
            )
        if record.status is IdempotencyStatus.COMPLETED and record.response_body:
            data = record.response_body.get("data")
            if isinstance(data, dict):
                return cast(dict[str, object], data)
        raise AppException(
            code="IDEMPOTENCY_IN_PROGRESS",
            message="相同幂等请求仍在处理中",
            status_code=409,
        )

    async def complete(
        self,
        context: AuthContext,
        cooperative_id: UUID,
        endpoint: str,
        idempotency_key: str,
        payload: BaseSchema,
        data: dict[str, object],
    ) -> None:
        record = await self.repository.claim(
            cooperative_id=cooperative_id,
            user_id=context.user_id,
            endpoint=endpoint,
            idempotency_key=idempotency_key,
            request_hash=request_hash_for(payload),
            expires_at=utc_now() + timedelta(days=7),
        )
        await self.repository.complete(
            record[0], response_status=201, response_body={"data": jsonable_encoder(data)}
        )


def request_hash_for(payload: BaseSchema) -> str:
    encoded = json.dumps(
        payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_hex(encoded)


__all__ = ["InventoryIdempotency", "request_hash_for"]
