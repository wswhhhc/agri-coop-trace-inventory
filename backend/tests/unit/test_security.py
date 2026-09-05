from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.core.security import (
    create_access_token,
    decode_jwt,
    hash_password,
    verify_password,
)

SECRET_KEY = "unit-test-secret-with-at-least-32-bytes"


def _token(**overrides: object) -> str:
    values: dict[str, object] = {
        "subject": "user-1",
        "session_id": "session-1",
        "role": "COOPERATIVE_ADMIN",
        "cooperative_id": "cooperative-1",
        "secret_key": SECRET_KEY,
        "issuer": "agri-api",
        "audience": "agri-web",
    }
    values.update(overrides)
    return create_access_token(**values)


def test_hash_password_and_verify_password() -> None:
    password = "correct horse battery staple"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2")
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong password", password_hash) is False


def test_verify_password_returns_false_for_malformed_hash() -> None:
    assert verify_password("password", "not-a-password-hash") is False


def test_create_and_decode_access_token() -> None:
    token = _token()

    claims = decode_jwt(
        token,
        secret_key=SECRET_KEY,
        issuer="agri-api",
        audience="agri-web",
    )

    assert claims["sub"] == "user-1"
    assert claims["sid"] == "session-1"
    assert claims["jti"]
    assert claims["role"] == "COOPERATIVE_ADMIN"
    assert claims["cooperativeId"] == "cooperative-1"
    assert isinstance(claims["iat"], int)
    assert isinstance(claims["exp"], int)
    assert claims["exp"] > claims["iat"]
    assert claims["iss"] == "agri-api"
    assert claims["aud"] == "agri-web"


def test_decode_jwt_rejects_expired_token() -> None:
    now = datetime.now(UTC)
    token = _token(now=now - timedelta(minutes=2), expires_minutes=1)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_jwt(token, secret_key=SECRET_KEY, issuer="agri-api", audience="agri-web")


def test_decode_jwt_rejects_invalid_signature() -> None:
    token = _token()

    with pytest.raises(jwt.InvalidSignatureError):
        decode_jwt(
            token,
            secret_key="another-secret-with-at-least-32-bytes",
            issuer="agri-api",
            audience="agri-web",
        )


def test_decode_jwt_rejects_invalid_issuer() -> None:
    token = _token()

    with pytest.raises(jwt.InvalidIssuerError):
        decode_jwt(token, secret_key=SECRET_KEY, issuer="another-api", audience="agri-web")


def test_decode_jwt_rejects_invalid_audience() -> None:
    token = _token()

    with pytest.raises(jwt.InvalidAudienceError):
        decode_jwt(token, secret_key=SECRET_KEY, issuer="agri-api", audience="another-web")


def test_decode_jwt_requires_application_claims() -> None:
    now = datetime.now(UTC)
    payload = {
        "sub": "user-1",
        "sid": "session-1",
        "jti": "token-1",
        "role": "COOPERATIVE_ADMIN",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "iss": "agri-api",
        "aud": "agri-web",
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    with pytest.raises(jwt.MissingRequiredClaimError, match="cooperativeId"):
        decode_jwt(token, secret_key=SECRET_KEY, issuer="agri-api", audience="agri-web")
