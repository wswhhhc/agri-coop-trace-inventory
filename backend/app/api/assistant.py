from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.memory import ShortConversationMemory
from app.assistant.schemas import AssistantQueryRequest
from app.assistant.service import AssistantService, encode_sse
from app.core.auth.dependencies import CurrentAuthContext
from app.core.config import Settings, get_settings
from app.infrastructure.database import get_db_session

router = APIRouter(prefix="/assistant", tags=["assistant"])
logger = logging.getLogger(__name__)
memory = ShortConversationMemory()


def get_assistant_service(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: CurrentAuthContext,
) -> AssistantService:
    return AssistantService(settings, session, context, memory)


@router.post(
    "/query",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {"schema": {"type": "string"}}}}},
)
async def query_assistant(
    payload: AssistantQueryRequest,
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        yield encode_sse(
            "start",
            {
                "conversationId": payload.conversation_id,
                "maxTurns": service.memory.max_turns,
            },
        )
        try:
            async for event in service.stream(payload.conversation_id, payload.message):
                event_type = str(event.pop("type", "message"))
                yield encode_sse(event_type, event)
        except Exception as error:
            logger.exception("assistant query failed")
            message = (
                str(error)
                if isinstance(error, RuntimeError)
                and str(error).startswith("尚未配置 AI_API_KEY")
                else "智能查询服务暂不可用，请稍后重试。"
            )
            yield encode_sse(
                "error",
                {"code": "ASSISTANT_QUERY_FAILED", "message": message},
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


__all__ = ["get_assistant_service", "router"]
