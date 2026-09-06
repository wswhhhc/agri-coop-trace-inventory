from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
from app.core.auth.context import AuthContext
from app.core.auth.dependencies import get_auth_context
from app.core.config import Settings
from app.infrastructure.database import get_db_session
from app.main import create_app
from app.models import AuditLog, Cooperative, Role, User
from fastapi.routing import APIRoute

pytestmark = pytest.mark.postgres


def test_audit_log_routes_are_read_only() -> None:
    from app.api.audit_logs import router

    routes = [route for route in router.routes if isinstance(route, APIRoute)]
    assert {(route.path, method) for route in routes for method in route.methods} == {
        ("/audit-logs", "GET"),
        ("/audit-logs/{auditLogId}", "GET"),
    }


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
    )


def _context(
    *,
    user_id: UUID,
    role_code: str,
    cooperative_id: UUID | None,
    permissions: frozenset[str] = frozenset({"audit:read"}),
) -> AuthContext:
    return AuthContext(
        user_id=user_id,
        username="audit-reader",
        real_name="审计查询用户",
        role_code=role_code,
        permission_codes=permissions,
        cooperative_id=cooperative_id,
        warehouse_ids=None,
        session_id="audit-session",
        token_id="audit-token",
    )


@pytest_asyncio.fixture
async def audit_log_api(postgres_session_factory):
    async with postgres_session_factory() as session:
        now = datetime.now(UTC)
        first_cooperative = Cooperative(code="AUDIT-ONE", name="第一审计合作社")
        second_cooperative = Cooperative(code="AUDIT-TWO", name="第二审计合作社")
        admin_role = Role(code="COOPERATIVE_ADMIN", name="合作社管理员")
        staff_role = Role(code="WAREHOUSE_STAFF", name="仓库工作人员")
        first_admin = User(
            cooperative=first_cooperative,
            role=admin_role,
            username="audit-admin",
            password_hash="not-used",
            real_name="审计管理员",
        )
        first_staff = User(
            cooperative=first_cooperative,
            role=staff_role,
            username="audit-staff",
            password_hash="not-used",
            real_name="审计仓库员",
        )
        second_user = User(
            cooperative=second_cooperative,
            role=staff_role,
            username="other-audit-user",
            password_hash="not-used",
            real_name="其他合作社用户",
        )
        second_log = AuditLog(
            cooperative_id=second_cooperative.id,
            user_id=second_user.id,
            action="DELETE",
            module="USER",
            object_type="USER",
            object_id=uuid4(),
            result="FAILURE",
            request_id="audit-3",
            detail={"password": "secret"},
            created_at=now,
        )
        session.add_all(
            [
                first_cooperative,
                second_cooperative,
                admin_role,
                staff_role,
                first_admin,
                first_staff,
                second_user,
            ]
        )
        await session.flush()
        first_object_id = uuid4()
        first_log = AuditLog(
            cooperative_id=first_cooperative.id,
            user_id=first_admin.id,
            action="UPDATE",
            module="INVENTORY",
            object_type="BATCH",
            object_id=first_object_id,
            result="SUCCESS",
            request_id="audit-1",
            ip_address="192.168.10.12",
            user_agent="sensitive-client",
            detail={"quantity": 12, "metadata": {"access_token": "secret"}},
            created_at=now - timedelta(minutes=2),
        )
        session.add_all(
            [
                first_log,
                AuditLog(
                    cooperative_id=first_cooperative.id,
                    user_id=first_staff.id,
                    action="READ",
                    module="INVENTORY",
                    object_type="BATCH",
                    object_id=uuid4(),
                    result="SUCCESS",
                    request_id="audit-2",
                    detail={"page": 1},
                    created_at=now - timedelta(minutes=1),
                ),
                second_log,
            ]
        )
        await session.commit()
        ids = {
            "first_cooperative": first_cooperative.id,
            "first_admin": first_admin.id,
            "first_staff": first_staff.id,
            "first_object": first_object_id,
            "second_log": second_log.id,
        }

    current_context = _context(
        user_id=ids["first_admin"],
        role_code="COOPERATIVE_ADMIN",
        cooperative_id=ids["first_cooperative"],
    )

    async def override_db_session():
        async with postgres_session_factory() as session:
            yield session

    async def override_auth_context() -> AuthContext:
        return current_context

    def set_context(context: AuthContext) -> None:
        nonlocal current_context
        current_context = context

    application = create_app(_settings())
    application.dependency_overrides[get_db_session] = override_db_session
    application.dependency_overrides[get_auth_context] = override_auth_context
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ids, set_context


@pytest.mark.asyncio
async def test_audit_log_list_paginates_filters_scopes_and_redacts(audit_log_api) -> None:
    client, ids, _ = audit_log_api

    response = await client.get("/api/v1/audit-logs?page=1&pageSize=1")

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"] == {
        "page": 1,
        "pageSize": 1,
        "totalItems": 2,
        "totalPages": 2,
    }
    item = body["data"][0]
    assert item["requestId"] == "audit-2"
    assert "ipAddress" not in item
    assert "userAgent" not in item

    first_page = await client.get("/api/v1/audit-logs?sortOrder=ASC")
    assert first_page.status_code == 200
    first_item = first_page.json()["data"][0]
    assert first_item["requestId"] == "audit-1"
    assert first_item["detail"]["metadata"]["access_token"] == "[REDACTED]"

    filtered = await client.get(
        "/api/v1/audit-logs",
        params={
            "action": "UPDATE",
            "resourceType": "BATCH",
            "resourceId": str(ids["first_object"]),
            "result": "SUCCESS",
            "startDate": "2020-01-01T00:00:00+00:00",
            "endDate": "2030-01-01T00:00:00+00:00",
        },
    )
    assert filtered.status_code == 200
    assert [item["requestId"] for item in filtered.json()["data"]] == ["audit-1"]


@pytest.mark.asyncio
async def test_audit_log_staff_is_forced_to_current_user(audit_log_api) -> None:
    client, ids, set_context = audit_log_api
    set_context(
        _context(
            user_id=ids["first_staff"],
            role_code="WAREHOUSE_STAFF",
            cooperative_id=ids["first_cooperative"],
        )
    )

    response = await client.get(f"/api/v1/audit-logs?userId={ids['first_admin']}")

    assert response.status_code == 200
    assert response.json()["pagination"]["totalItems"] == 1
    assert response.json()["data"][0]["userId"] == str(ids["first_staff"])


@pytest.mark.asyncio
async def test_audit_log_requires_permission_and_hides_cross_cooperative_detail(
    audit_log_api,
) -> None:
    client, ids, set_context = audit_log_api
    set_context(
        _context(
            user_id=ids["first_admin"],
            role_code="COOPERATIVE_ADMIN",
            cooperative_id=ids["first_cooperative"],
            permissions=frozenset(),
        )
    )
    forbidden = await client.get("/api/v1/audit-logs")
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "PERMISSION_DENIED"

    set_context(
        _context(
            user_id=ids["first_admin"],
            role_code="COOPERATIVE_ADMIN",
            cooperative_id=ids["first_cooperative"],
        )
    )
    hidden = await client.get(f"/api/v1/audit-logs/{ids['second_log']}")
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_audit_log_system_admin_can_read_global_detail_and_invalid_range_is_rejected(
    audit_log_api,
) -> None:
    client, ids, set_context = audit_log_api
    set_context(
        _context(
            user_id=ids["first_admin"],
            role_code="SYSTEM_ADMIN",
            cooperative_id=None,
        )
    )

    global_logs = await client.get("/api/v1/audit-logs?pageSize=10")
    assert global_logs.status_code == 200
    assert global_logs.json()["pagination"]["totalItems"] == 3

    detail = await client.get(f"/api/v1/audit-logs/{ids['second_log']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["detail"]["password"] == "[REDACTED]"
    assert "ipAddress" not in detail.json()["data"]

    invalid_range = await client.get(
        "/api/v1/audit-logs",
        params={
            "startDate": "2030-01-01T00:00:00+00:00",
            "endDate": "2020-01-01T00:00:00+00:00",
        },
    )
    assert invalid_range.status_code == 422
