from __future__ import annotations

from uuid import uuid4

from pydantic import Field

from app.schemas.common import BaseSchema


class AssistantQueryRequest(BaseSchema):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class AssistantQueryContext(BaseSchema):
    """仅用于内部工具结果，避免把 ORM 对象直接交给模型。"""

    resource: str
    total_items: int = Field(ge=0)
    items: list[dict[str, object]]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class AssistantConversationInfo(BaseSchema):
    conversation_id: str
    turns_used: int = Field(ge=0, le=3)
    max_turns: int = 3


class AssistantDoneData(BaseSchema):
    conversation: AssistantConversationInfo
    data: AssistantQueryContext | None = None


__all__ = [
    "AssistantConversationInfo",
    "AssistantDoneData",
    "AssistantQueryContext",
    "AssistantQueryRequest",
]
