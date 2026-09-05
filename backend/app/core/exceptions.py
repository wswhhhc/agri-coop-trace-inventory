from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, cast
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.schemas.common import ErrorInfo, ErrorResponse

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")

_STATUS_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "AUTHENTICATION_REQUIRED",
    403: "PERMISSION_DENIED",
    404: "RESOURCE_NOT_FOUND",
    409: "RESOURCE_CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    503: "DEPENDENCY_UNAVAILABLE",
}
_STATUS_MESSAGES: dict[int, str] = {
    400: "请求语义错误",
    401: "缺少有效身份信息",
    403: "缺少执行该操作的权限",
    404: "资源不存在或不可见",
    409: "资源状态或唯一性冲突",
    422: "请求字段校验失败",
    429: "请求过于频繁",
    503: "依赖服务暂时不可用",
}
_STARLETTE_DEFAULT_MESSAGES = {
    "Bad Request",
    "Unauthorized",
    "Forbidden",
    "Not Found",
    "Conflict",
    "Unprocessable Entity",
    "Too Many Requests",
    "Service Unavailable",
}


class AppException(Exception):
    """可安全返回给客户端的业务异常。"""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = dict(details or {})
        self.headers = dict(headers or {})


def _is_valid_request_id(value: str | None) -> bool:
    return value is not None and _REQUEST_ID_PATTERN.fullmatch(value) is not None


def _get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and _is_valid_request_id(request_id):
        return request_id
    return f"req_{uuid4().hex}"


async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """为每个请求建立可追踪的请求 ID，并写回所有响应。"""
    request_id = request.headers.get(REQUEST_ID_HEADER)
    if not isinstance(request_id, str) or not _is_valid_request_id(request_id):
        request_id = f"req_{uuid4().hex}"
    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception:  # noqa: BLE001 - global HTTP boundary must catch unknown errors
        # ServerErrorMiddleware 会重新抛出未处理异常，直接在最外层兜底，
        # 才能保证自定义 500 响应和 X-Request-ID 一起返回给客户端。
        response = _error_response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="服务暂时不可用，请稍后重试",
        )
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorInfo(
            code=code,
            message=message,
            details=dict(details or {}),
            request_id=_get_request_id(request),
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body, by_alias=True),
        headers=dict(headers or {}),
    )


def _http_exception_message(status_code: int, detail: Any) -> str:
    if isinstance(detail, str) and detail and detail not in _STARLETTE_DEFAULT_MESSAGES:
        return detail
    return _STATUS_MESSAGES.get(status_code, "请求处理失败")


def _validation_details(exc: RequestValidationError) -> dict[str, Any]:
    fields: list[dict[str, str]] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()))
        field_error = {
            "field": location,
            "message": str(error.get("msg", "字段值无效")),
            "type": str(error.get("type", "invalid")),
        }
        fields.append(field_error)
    return {"fields": fields}


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return _error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = _STATUS_CODES.get(exc.status_code, "HTTP_ERROR")
    details: dict[str, Any] = exc.detail if isinstance(exc.detail, dict) else {}
    return _error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=_http_exception_message(exc.status_code, exc.detail),
        details=details,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="请求字段校验失败",
        details=_validation_details(exc),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "未处理的服务端异常 request_id=%s method=%s path=%s",
        _get_request_id(request),
        request.method,
        request.url.path,
    )
    return _error_response(
        request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="服务暂时不可用，请稍后重试",
    )


def register_exception_handlers(application: FastAPI) -> None:
    """注册全局异常处理器，确保所有错误符合公共错误契约。"""
    application.add_exception_handler(
        AppException, cast(Any, app_exception_handler)
    )
    application.add_exception_handler(
        StarletteHTTPException, cast(Any, http_exception_handler)
    )
    application.add_exception_handler(
        RequestValidationError, cast(Any, validation_exception_handler)
    )
    application.add_exception_handler(Exception, unhandled_exception_handler)


__all__ = [
    "REQUEST_ID_HEADER",
    "AppException",
    "app_exception_handler",
    "http_exception_handler",
    "register_exception_handlers",
    "request_id_middleware",
    "unhandled_exception_handler",
    "validation_exception_handler",
]
