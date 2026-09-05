from __future__ import annotations

from typing import Any

from app import main
from app.core.config import Settings
from app.core.exceptions import AppException
from fastapi import HTTPException, Query
from fastapi.testclient import TestClient


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "jwt_secret_key": "unit-test-secret",
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
