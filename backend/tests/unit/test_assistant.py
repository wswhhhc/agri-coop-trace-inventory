from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.api.assistant import get_assistant_service
from app.assistant.memory import ShortConversationMemory
from app.assistant.service import AssistantService, encode_sse
from app.assistant.tools import QueryToolFactory
from app.core.auth.context import AuthContext
from app.main import create_app
from fastapi.testclient import TestClient


def _context(*permissions: str, role: str = "WAREHOUSE_STAFF") -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        username="staff01",
        real_name="仓库员工",
        role_code=role,
        permission_codes=frozenset(permissions),
        cooperative_id=uuid4(),
        warehouse_ids=frozenset({uuid4()}),
        session_id="session",
        token_id="token",
    )


def test_short_memory_keeps_only_three_turns() -> None:
    memory = ShortConversationMemory()
    for index in range(4):
        memory.append("conversation", f"问题{index}", f"回答{index}")

    assert memory.history("conversation") == [
        {"role": "user", "content": "问题1"},
        {"role": "assistant", "content": "回答1"},
        {"role": "user", "content": "问题2"},
        {"role": "assistant", "content": "回答2"},
        {"role": "user", "content": "问题3"},
        {"role": "assistant", "content": "回答3"},
    ]


def test_sse_event_is_json_and_utf8_friendly() -> None:
    event = encode_sse("token", {"content": "查询完成"})

    assert event.startswith("event: token\ndata: ")
    assert event.endswith("\n\n")
    assert "查询完成" in event


def test_query_tools_follow_role_permissions() -> None:
    staff_tools = QueryToolFactory(
        None,  # type: ignore[arg-type]
        _context("inventory:read", "alert:read", "model:read"),
    ).build()
    staff_names = {item.name for item in staff_tools}

    assert staff_names == {
        "query_warehouses",
        "query_products",
        "query_batches",
        "query_inventories",
        "query_inventory_transactions",
        "query_alerts",
        "query_model_versions",
        "query_forecast_results",
    }


def test_user_and_cooperative_tools_are_not_exposed_without_manage_permissions() -> (
    None
):
    tools = QueryToolFactory(None, _context("inventory:read")).build()  # type: ignore[arg-type]

    assert {item.name for item in tools}.isdisjoint(
        {"query_users", "query_cooperatives"}
    )


def test_assistant_query_route_is_documented_as_sse() -> None:
    operation = create_app().openapi()["paths"]["/api/v1/assistant/query"]["post"]

    assert operation["responses"]["200"]["content"]["text/event-stream"]


def test_assistant_query_route_streams_sse_events() -> None:
    class FakeService:
        memory = SimpleNamespace(max_turns=3)

        async def stream(self, _conversation_id: str, _message: str):
            yield {"type": "token", "content": "查询完成"}
            yield {
                "type": "done",
                "conversationId": "c1",
                "turnsUsed": 1,
                "maxTurns": 3,
            }

    application = create_app()
    application.dependency_overrides[get_assistant_service] = lambda: FakeService()

    response = TestClient(application).post(
        "/api/v1/assistant/query",
        json={"message": "查询库存", "conversationId": "c1"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: token" in response.text
    assert "event: done" in response.text


@pytest.mark.asyncio
async def test_stream_emits_tokens_and_binds_memory_to_user() -> None:
    class FakeToken:
        text = "查询完成"

    class FakeAgent:
        async def astream(self, *_args, **_kwargs):
            yield {
                "type": "messages",
                "data": (FakeToken(), {"langgraph_node": "model"}),
            }

    context = _context("inventory:read")
    service = AssistantService(
        SimpleNamespace(),
        None,
        context,
        ShortConversationMemory(),  # type: ignore[arg-type]
    )
    service._agent = lambda: FakeAgent()  # type: ignore[method-assign]

    events = [event async for event in service.stream("same-id", "查询库存")]

    assert events[0] == {"type": "token", "content": "查询完成"}
    assert events[1]["type"] == "done"
    assert service.memory.history(service._memory_key("same-id"))
