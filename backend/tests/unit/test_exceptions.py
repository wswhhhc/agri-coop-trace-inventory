from __future__ import annotations

from typing import Any

from app import main
from app.core.config import Settings
from app.core.exceptions import (
    AppException,
    BatchNotFoundError,
    DataScopeAccessDeniedError,
    ForeignKeyConflictError,
    InsufficientInventoryError,
    StatusNotAllowedError,
    UniqueConflictError,
)
from fastapi import HTTPException, Query
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "jwt_secret_key": "unit-test-secret-with-at-least-32-bytes",
        "jwt_issuer": "agri-api",
        "jwt_audience": "agri-web",
        "postgres_password": "unit-test-password",
    }
    values.update(overrides)
    return Settings(**values)


def _client() -> TestClient:
    return TestClient(main.create_app(_settings()), raise_server_exceptions=False)


def test_health_response_is_wrapped_and_contains_request_id() -> None:
    client = _client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "data": {"status": "ok", "environment": "development"}
    }
    assert response.headers["X-Request-ID"].startswith("req_")


def test_client_request_id_is_reused_in_response_and_error_body() -> None:
    client = _client()

    response = client.get("/missing", headers={"X-Request-ID": "req_client_123"})

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "req_client_123"
    assert response.json() == {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "资源不存在或不可见",
            "details": {},
            "requestId": "req_client_123",
        }
    }


def test_http_exception_is_converted_to_common_error_shape() -> None:
    app = main.create_app(_settings())

    @app.get("/rate-limited")
    async def rate_limited() -> None:
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁",
            headers={"Retry-After": "30"},
        )

    response = TestClient(app, raise_server_exceptions=False).get("/rate-limited")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "30"
    assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_app_exception_is_converted_to_common_error_shape() -> None:
    app = main.create_app(_settings())

    @app.get("/business-error")
    async def business_error() -> None:
        raise AppException(
            code="RESOURCE_CONFLICT",
            message="资源状态冲突",
            status_code=409,
            details={"field": "status"},
        )

    response = TestClient(app, raise_server_exceptions=False).get("/business-error")

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "RESOURCE_CONFLICT",
        "message": "资源状态冲突",
        "details": {"field": "status"},
        "requestId": response.headers["X-Request-ID"],
    }


def test_validation_error_is_sanitized_and_uses_common_error_shape() -> None:
    app = main.create_app(_settings())

    @app.get("/items")
    async def list_items(limit: int = Query(ge=1)) -> dict[str, Any]:
        return {"limit": limit}

    response = TestClient(app, raise_server_exceptions=False).get("/items?limit=0")

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "请求字段校验失败"
    assert body["error"]["requestId"] == response.headers["X-Request-ID"]
    assert body["error"]["details"]["fields"] == [
        {
            "field": "query.limit",
            "message": "Input should be greater than or equal to 1",
            "type": "greater_than_equal",
        }
    ]
    assert "input" not in body["error"]["details"]["fields"][0]


def test_unexpected_exception_does_not_leak_internal_message() -> None:
    app = main.create_app(_settings())

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("database password should not be returned")

    response = TestClient(app, raise_server_exceptions=False).get("/unexpected")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "服务暂时不可用，请稍后重试",
            "details": {},
            "requestId": response.headers["X-Request-ID"],
        }
    }
    assert "password" not in response.text


def test_business_exception_categories_have_stable_http_contract() -> None:
    cases = [
        (BatchNotFoundError("batch-1"), "BATCH_NOT_FOUND", 404),
        (InsufficientInventoryError(), "INSUFFICIENT_INVENTORY", 409),
        (StatusNotAllowedError(), "STATUS_NOT_ALLOWED", 409),
        (DataScopeAccessDeniedError(), "SCOPE_ACCESS_DENIED", 403),
        (UniqueConflictError(), "UNIQUE_CONFLICT", 409),
        (ForeignKeyConflictError(), "FOREIGN_KEY_CONFLICT", 409),
    ]

    for exception, code, status_code in cases:
        assert exception.code == code
        assert exception.status_code == status_code


class _PostgresError(Exception):
    def __init__(self, *, sqlstate: str, constraint_name: str) -> None:
        super().__init__(constraint_name)
        self.sqlstate = sqlstate
        self.constraint_name = constraint_name


def _integrity_error(*, sqlstate: str, constraint_name: str) -> IntegrityError:
    return IntegrityError(
        "INSERT INTO demo VALUES (...)",
        {},
        _PostgresError(sqlstate=sqlstate, constraint_name=constraint_name),
    )


def test_unique_integrity_error_returns_explicit_conflict_code() -> None:
    app = main.create_app(_settings())

    @app.get("/database-unique-error")
    async def database_unique_error() -> None:
        raise _integrity_error(
            sqlstate="23505", constraint_name="uq_products_cooperative_code"
        )

    response = TestClient(app, raise_server_exceptions=False).get(
        "/database-unique-error", headers={"X-Request-ID": "req_unique_1"}
    )

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "UNIQUE_CONFLICT",
        "message": "数据唯一性冲突",
        "details": {},
        "requestId": "req_unique_1",
    }


def test_foreign_key_integrity_error_returns_explicit_conflict_code() -> None:
    app = main.create_app(_settings())

    @app.get("/database-foreign-key-error")
    async def database_foreign_key_error() -> None:
        raise _integrity_error(
            sqlstate="23503", constraint_name="fk_batches_product_id"
        )

    response = TestClient(app, raise_server_exceptions=False).get(
        "/database-foreign-key-error"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "FOREIGN_KEY_CONFLICT"
    assert response.json()["error"]["requestId"] == response.headers["X-Request-ID"]


def test_unknown_database_error_is_logged_and_returns_internal_error(caplog) -> None:
    app = main.create_app(_settings())

    @app.get("/database-unknown-error")
    async def database_unknown_error() -> None:
        raise SQLAlchemyError("database password should not leak")

    with caplog.at_level("ERROR"):
        response = TestClient(app, raise_server_exceptions=False).get(
            "/database-unknown-error"
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "DATABASE_ERROR"
    assert response.json()["error"]["requestId"] == response.headers["X-Request-ID"]
    assert "database-unknown-error" in caplog.text
    assert "database password should not leak" in caplog.text
