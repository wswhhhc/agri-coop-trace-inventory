from __future__ import annotations

from dataclasses import dataclass

from starlette.requests import Request


@dataclass(frozen=True, slots=True)
class AuditContext:
    """安全事件的请求级关联信息，不包含密码、令牌或 Cookie。"""

    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    @classmethod
    def from_request(cls, request: Request) -> AuditContext:
        client_ip = request.client.host if request.client is not None else None
        user_agent = request.headers.get("user-agent")
        return cls(
            request_id=getattr(request.state, "request_id", None),
            ip_address=client_ip,
            user_agent=user_agent[:500] if user_agent is not None else None,
        )
