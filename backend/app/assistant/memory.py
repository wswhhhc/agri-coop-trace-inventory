from __future__ import annotations

from collections import OrderedDict, deque
from threading import Lock


class ShortConversationMemory:
    """进程内短记忆：每个会话只保留最近三轮问答。"""

    def __init__(self, max_turns: int = 3, max_conversations: int = 512) -> None:
        self.max_turns = max_turns
        self.max_conversations = max_conversations
        self._items: OrderedDict[str, deque[dict[str, str]]] = OrderedDict()
        self._lock = Lock()

    def history(self, conversation_id: str) -> list[dict[str, str]]:
        with self._lock:
            messages = self._items.get(conversation_id)
            if messages is None:
                return []
            self._items.move_to_end(conversation_id)
            return list(messages)

    def append(
        self, conversation_id: str, user_message: str, assistant_message: str
    ) -> int:
        with self._lock:
            messages = self._items.setdefault(
                conversation_id, deque(maxlen=self.max_turns * 2)
            )
            messages.extend(
                (
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message},
                )
            )
            self._items.move_to_end(conversation_id)
            while len(self._items) > self.max_conversations:
                self._items.popitem(last=False)
            return len(messages) // 2

    def clear(self, conversation_id: str) -> None:
        with self._lock:
            self._items.pop(conversation_id, None)


__all__ = ["ShortConversationMemory"]
