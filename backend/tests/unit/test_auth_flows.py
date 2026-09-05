from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.core.auth.flows import AuthenticationService
from app.core.auth.session import AuthSession, CreatedSession
from app.core.exceptions import AppException
from app.core.security import hash_password

SECRET_KEY = "unit-test-secret-with-at-least-32-bytes"


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        jwt_secret_key=SimpleNamespace(get_secret_value=lambda: SECRET_KEY),
        jwt_algorithm="HS256",
        jwt_issuer=None,
        jwt_audience=None,
        access_token_expire_minutes=30,
    )


def _user(*, status: str = "ACTIVE", password: str = "correct-password") -> SimpleNamespace:
    cooperative = SimpleNamespace(id=uuid4(), status="ACTIVE")
    role = SimpleNamespace(
        code="COOPERATIVE_ADMIN",
        permissions=[SimpleNamespace(code="inventory:read")],
    )
    return SimpleNamespace(
        id=uuid4(),
        username="coop_admin",
        real_name="合作社管理员",
        password_hash=hash_password(password),
        status=status,
        cooperative_id=cooperative.id,
        cooperative=cooperative,
        role=role,
        last_login_at=None,
    )


class _FakeUserRepository:
    def __init__(self, user: SimpleNamespace | None) -> None:
        self.user = user

    async def get_by_username_with_access(self, _username: str):
        return self.user


class _FakeSessionStore:
    def __init__(self) -> None:
        self.created = CreatedSession(
            session=AuthSession(
                session_id="00000000-0000-0000-0000-000000000001",
                user_id=uuid4(),
                session_family="family-1",
                status="ACTIVE",
                refresh_token_hash="hash-1",
                created_at=datetime.now(UTC),
                last_rotated_at=datetime.now(UTC),
            ),
            refresh_token="v1.00000000-0000-0000-0000-000000000001.refresh-token",
        )

    async def create(self, _user_id):
        return self.created


class _FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None


class _FakeSession:
    def begin(self):
        return _FakeTransaction()


class _FakeAuditLogService:
    def __init__(self) -> None:
        self.events = []

    async def record(self, event) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_login_uses_same_error_for_unknown_username_and_wrong_password() -> None:
    user = _user()
    audit_service = _FakeAuditLogService()
    service = AuthenticationService(
        _FakeSession(),
        _settings(),
        _FakeSessionStore(),
        audit_log_service=audit_service,
    )
    service.user_repository = _FakeUserRepository(None)

    with pytest.raises(AppException) as unknown:
        await service.login("unknown", "wrong-password")

    service.user_repository = _FakeUserRepository(user)
    with pytest.raises(AppException) as wrong_password:
        await service.login("coop_admin", "wrong-password")

    assert (
        unknown.value.status_code,
        unknown.value.code,
        unknown.value.message,
    ) == (
        wrong_password.value.status_code,
        wrong_password.value.code,
        wrong_password.value.message,
    )
    assert [event.detail["reason"] for event in audit_service.events] == [
        "invalid_credentials",
        "invalid_credentials",
    ]


@pytest.mark.asyncio
async def test_successful_login_records_audit_event_without_credentials() -> None:
    user = _user()
    audit_service = _FakeAuditLogService()
    service = AuthenticationService(
        _FakeSession(),
        _settings(),
        _FakeSessionStore(),
        audit_log_service=audit_service,
    )
    service.user_repository = _FakeUserRepository(user)

    await service.login("coop_admin", "correct-password")

    assert len(audit_service.events) == 1
    event = audit_service.events[0]
    assert event.action == "LOGIN"
    assert event.result == "SUCCESS"
    assert event.user_id == user.id
    assert event.detail == {}


@pytest.mark.asyncio
async def test_locked_user_cannot_login() -> None:
    service = AuthenticationService(_FakeSession(), _settings(), _FakeSessionStore())
    service.user_repository = _FakeUserRepository(_user(status="LOCKED"))

    with pytest.raises(AppException) as error:
        await service.login("coop_admin", "correct-password")

    assert error.value.code == "ACCOUNT_LOCKED"
    assert error.value.status_code == 403
