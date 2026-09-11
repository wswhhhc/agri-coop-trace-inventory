from __future__ import annotations

from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import ApiResponse, BaseSchema


class LoginRequest(BaseSchema):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseSchema):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_password_change(self) -> ChangePasswordRequest:
        if self.current_password == self.new_password:
            raise ValueError("新密码不能与当前密码相同")
        return self


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


class CurrentUserData(BaseSchema):
    id: UUID
    username: str
    display_name: str
    role: str
    cooperative_id: UUID | None
    warehouse_ids: list[UUID] | None
    permissions: list[str]
    status: str


AuthTokenResponse = ApiResponse[AuthTokenData]


__all__ = [
    "AuthTokenData",
    "AuthTokenResponse",
    "AuthUser",
    "ChangePasswordRequest",
    "CurrentUserData",
    "LoginRequest",
]
