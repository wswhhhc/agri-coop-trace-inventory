from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.api.traceability import (
    _check_public_rate_limit,
    build_public_trace_url,
    get_public_qr_code,
)
from app.core.auth.public_rate_limit import (
    PublicRateLimiter,
    PublicRateLimiterDependencyError,
    PublicRateLimitExceeded,
)
from app.core.config import Settings
from app.core.exceptions import AppException
from fastapi import Request


class ScriptRedis:
    def __init__(self) -> None:
        self.count = 0

    async def eval(self, script: str, key_count: int, key: str, window: str):
        self.count += 1
        return [self.count, int(window)]


class BrokenRedis:
    async def eval(self, *args):
        raise RuntimeError("redis unavailable")


def _request(client_ip: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/public/traces/tr_abc",
            "headers": [],
            "client": (client_ip, 1234),
            "server": ("test", 80),
            "scheme": "http",
        }
    )


@pytest.mark.asyncio
async def test_public_rate_limiter_blocks_after_configured_requests() -> None:
    limiter = PublicRateLimiter(
        ScriptRedis(), key_prefix="test:", resource="trace", max_requests=2
    )

    await limiter.ensure_allowed("192.0.2.1")
    await limiter.ensure_allowed("192.0.2.1")
    with pytest.raises(PublicRateLimitExceeded) as error:
        await limiter.ensure_allowed("192.0.2.1")

    assert error.value.retry_after == 60
    assert limiter._key("192.0.2.1").startswith("test:public:trace:ip:")


@pytest.mark.asyncio
async def test_public_rate_limiter_reports_dependency_failure() -> None:
    limiter = PublicRateLimiter(
        BrokenRedis(), key_prefix="test:", resource="qr", max_requests=2
    )

    with pytest.raises(PublicRateLimiterDependencyError):
        await limiter.ensure_allowed("192.0.2.1")


@pytest.mark.asyncio
async def test_api_rate_limit_mapping_returns_stable_error_contract() -> None:
    limiter = PublicRateLimiter(
        ScriptRedis(), key_prefix="test:", resource="trace", max_requests=1
    )
    request = _request("192.0.2.1")
    await _check_public_rate_limit(limiter, request)

    with pytest.raises(AppException) as error:
        await _check_public_rate_limit(limiter, request)

    assert error.value.status_code == 429
    assert error.value.code == "RATE_LIMIT_EXCEEDED"
    assert error.value.headers["Retry-After"] == "60"


def test_public_trace_url_contains_only_the_trace_code() -> None:
    settings = SimpleNamespace(public_trace_url="https://example.test/trace/")

    assert build_public_trace_url(settings, "tr_abc/secret") == (
        "https://example.test/trace/tr_abc%2Fsecret"
    )


@pytest.mark.asyncio
async def test_qr_endpoint_returns_png_after_validating_trace_code() -> None:
    settings = Settings(
        _env_file=None,
        jwt_secret_key="unit-test-secret-with-at-least-32-bytes",
        jwt_issuer="agri-api",
        jwt_audience="agri-web",
        postgres_password="unit-test-password",
        public_trace_url="https://example.test/trace",
    )
    service = SimpleNamespace(get_public=lambda trace_code: _completed(trace_code))
    response = await get_public_qr_code(
        "tr_abc",
        _request("192.0.2.2"),
        settings,
        PublicRateLimiter(
            ScriptRedis(), key_prefix="test:", resource="qr", max_requests=1
        ),
        service,
    )

    body = b"".join([chunk async for chunk in response.body_iterator])
    assert response.media_type == "image/png"
    assert body.startswith(b"\x89PNG\r\n\x1a\n")


async def _completed(trace_code: str) -> None:
    return None
