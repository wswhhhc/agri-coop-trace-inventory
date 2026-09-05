"""无业务安全工具：密码哈希和 JWT 操作。"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

_PASSWORD_HASH = PasswordHash.recommended()
_REQUIRED_APPLICATION_CLAIMS = ("sub", "sid", "jti", "role", "cooperativeId")
_REQUIRED_TIME_CLAIMS = ("iat", "exp")


def hash_password(password: str) -> str:
    """使用 Argon2 哈希密码。"""
    return _PASSWORD_HASH.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """校验密码；哈希格式无效时按校验失败处理。"""
    try:
        return _PASSWORD_HASH.verify(password, password_hash)
    except UnknownHashError:
        return False


def create_access_token(
    *,
    subject: str,
    session_id: str,
    role: str,
    cooperative_id: str | None,
    secret_key: str,
    algorithm: str = "HS256",
    expires_minutes: int = 30,
    issuer: str | None = None,
    audience: str | None = None,
    now: datetime | None = None,
    token_id: str | None = None,
) -> str:
    """签发包含应用必要 Claims 的访问令牌。"""
    _validate_required_string("subject", subject)
    _validate_required_string("session_id", session_id)
    _validate_required_string("role", role)
    if cooperative_id is not None:
        _validate_required_string("cooperative_id", cooperative_id)
    if not secret_key:
        raise ValueError("secret_key 不能为空")
    if not algorithm:
        raise ValueError("algorithm 不能为空")
    if expires_minutes <= 0:
        raise ValueError("expires_minutes 必须大于 0")

    issued_at = now or datetime.now(UTC)
    if issued_at.tzinfo is None:
        issued_at = issued_at.replace(tzinfo=UTC)
    issued_at = issued_at.astimezone(UTC)
    issued_at_timestamp = int(issued_at.timestamp())

    token_id = token_id or str(uuid4())
    _validate_required_string("token_id", token_id)

    payload: dict[str, Any] = {
        "sub": subject,
        "sid": session_id,
        "jti": token_id,
        "role": role,
        "cooperativeId": cooperative_id,
        "iat": issued_at_timestamp,
        "exp": issued_at_timestamp
        + int(timedelta(minutes=expires_minutes).total_seconds()),
    }
    if issuer is not None:
        _validate_required_string("issuer", issuer)
        payload["iss"] = issuer
    if audience is not None:
        _validate_required_string("audience", audience)
        payload["aud"] = audience

    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_jwt(
    token: str,
    *,
    secret_key: str,
    algorithm: str = "HS256",
    issuer: str | None = None,
    audience: str | None = None,
) -> dict[str, Any]:
    """解码并校验 JWT 的签名、时间、issuer、audience 和必要 Claims。"""
    if not token:
        raise jwt.InvalidTokenError("token 不能为空")
    if not secret_key:
        raise ValueError("secret_key 不能为空")
    if not algorithm:
        raise ValueError("algorithm 不能为空")

    # PyJWT 的 require 会把 None 视为缺失；cooperativeId 对系统管理员
    # 合法地允许为 null，因此只交给下方校验“必须存在”，不在这里要求非空。
    required_claims = [
        claim
        for claim in (*_REQUIRED_APPLICATION_CLAIMS, *_REQUIRED_TIME_CLAIMS)
        if claim != "cooperativeId"
    ]
    if issuer is not None:
        _validate_required_string("issuer", issuer)
        required_claims.append("iss")
    if audience is not None:
        _validate_required_string("audience", audience)
        required_claims.append("aud")

    claims = jwt.decode(
        token,
        secret_key,
        algorithms=[algorithm],
        issuer=issuer,
        audience=audience,
        options={"require": required_claims},
    )
    _validate_decoded_claims(claims)
    return claims


def _validate_required_string(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} 必须是非空字符串")


def _validate_decoded_claims(claims: Mapping[str, Any]) -> None:
    for name in _REQUIRED_APPLICATION_CLAIMS:
        if name not in claims:
            raise jwt.MissingRequiredClaimError(name)

    for name in ("sub", "sid", "jti", "role"):
        value = claims[name]
        if not isinstance(value, str) or not value.strip():
            raise jwt.InvalidTokenError(f"Claim {name} 必须是非空字符串")

    cooperative_id = claims["cooperativeId"]
    if cooperative_id is not None and (
        not isinstance(cooperative_id, str) or not cooperative_id.strip()
    ):
        raise jwt.InvalidTokenError("Claim cooperativeId 必须是字符串或 null")


__all__ = [
    "create_access_token",
    "decode_jwt",
    "hash_password",
    "verify_password",
]
