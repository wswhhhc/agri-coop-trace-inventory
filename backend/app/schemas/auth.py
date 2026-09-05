from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiResponse, BaseSchema


class LoginRequest(BaseSchema):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class AuthUser(BaseSchema):
    id: UUID
    username: str
    display_name: str
    role: str
    cooperative_id: UUID | None
    status: str


class AuthTokenData(BaseSchema):
    access_token: str
    token_type: str
    expires_in: int
    user: AuthUser
    permissions: list[str]


AuthTokenResponse = ApiResponse[AuthTokenData]


__all__ = [
    "AuthTokenData",
    "AuthTokenResponse",
    "AuthUser",
    "LoginRequest",
]
