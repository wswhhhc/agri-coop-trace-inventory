from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.memory import ShortConversationMemory
from app.assistant.tools import QueryToolFactory
from app.core.auth.context import AuthContext
from app.core.config import Settings

SYSTEM_PROMPT = """你是农业合作社追溯与库存系统的查询助手。
只回答当前登录用户有权限查询的数据。必须优先调用合适的查询工具，不得编造数据、ID、数量或日期。
如果用户的查询条件不明确，先用简短问题追问；如果工具返回空结果，明确告诉用户没有找到。
回答使用简洁中文，说明查询范围、结果数量，并根据数据给出必要的字段解释。
不要执行任何写入、修改、删除或导出操作；本助手当前仅支持只读查询。
"""


class AssistantService:
    def __init__(
        self,
        settings: Settings,
        session: AsyncSession,
        context: AuthContext,
        memory: ShortConversationMemory,
    ) -> None:
        self.settings = settings
        self.session = session
        self.context = context
        self.memory = memory

    def _agent(self) -> Any:
        if self.settings.ai_api_key is None:
            raise RuntimeError("尚未配置 AI_API_KEY，暂时无法使用智能查询")
        model = ChatOpenAI(
            api_key=self.settings.ai_api_key,
            model=self.settings.ai_model,
            base_url=self.settings.ai_base_url,
            timeout=self.settings.ai_timeout_seconds,
            max_retries=1,
        )
        return create_agent(
            model=model,
            tools=QueryToolFactory(self.session, self.context).build(),
            system_prompt=SYSTEM_PROMPT,
        )

    def _memory_key(self, conversation_id: str) -> str:
        """将会话绑定到当前用户，防止猜测会话 ID 读取他人上下文。"""
        return f"{self.context.user_id}:{conversation_id}"

    async def stream(
        self, conversation_id: str, message: str
    ) -> AsyncIterator[dict[str, object]]:
        memory_key = self._memory_key(conversation_id)
        history = self.memory.history(memory_key)
        agent = self._agent()
        full_response: list[str] = []
        async for chunk in agent.astream(
            {"messages": [*history, {"role": "user", "content": message}]},
            stream_mode=["messages", "updates"],
            version="v2",
            config={"recursion_limit": 8},
        ):
            chunk_type = chunk.get("type")
            if chunk_type == "updates":
                update_data = chunk.get("data", {})
                if isinstance(update_data, dict):
                    tool_update = update_data.get("tools")
                    if isinstance(tool_update, dict):
                        messages = tool_update.get("messages", [])
                        for tool_message in messages:
                            result = _parse_tool_result(getattr(tool_message, "content", None))
                            if result is not None:
                                yield {
                                    "type": "result",
                                    "resource": result.get("resource", ""),
                                    "totalItems": result.get("pagination", {}).get(
                                        "totalItems", 0
                                    ),
                                }
                continue
            if chunk_type != "messages":
                continue
            token, metadata = chunk["data"]
            if metadata.get("langgraph_node") != "model":
                continue
            text = getattr(token, "text", "")
            if not text:
                continue
            full_response.append(text)
            yield {"type": "token", "content": text}
        answer = "".join(full_response).strip()
        turns = self.memory.append(memory_key, message, answer)
        yield {
            "type": "done",
            "conversationId": conversation_id,
            "turnsUsed": turns,
            "maxTurns": self.memory.max_turns,
        }


def _parse_tool_result(content: Any) -> dict[str, Any] | None:
    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        return None
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) and "resource" in value else None


def encode_sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


__all__ = ["AssistantService", "encode_sse"]
