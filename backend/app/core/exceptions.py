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
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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


class BatchNotFoundError(AppException):
    """请求的农产品批次不存在。"""

    def __init__(self, batch_id: object | None = None) -> None:
        super().__init__(
            code="BATCH_NOT_FOUND",
            message="批次不存在",
            status_code=404,
            details=(
                {"batchId": str(batch_id)} if batch_id is not None else None
            ),
        )


class InsufficientInventoryError(AppException):
    """库存数量不足以完成当前业务操作。"""

    def __init__(
        self,
        *,
        available: object | None = None,
        requested: object | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if available is not None:
            details["available"] = available
        if requested is not None:
            details["requested"] = requested
        super().__init__(
            code="INSUFFICIENT_STOCK",
            message="库存不足",
            status_code=409,
            details=details,
        )


class StatusNotAllowedError(AppException):
    """资源当前状态不允许执行目标操作。"""

    def __init__(
        self,
        *,
        current_status: str | None = None,
        allowed_statuses: list[str] | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if current_status is not None:
            details["currentStatus"] = current_status
        if allowed_statuses is not None:
            details["allowedStatuses"] = allowed_statuses
        super().__init__(
            code="INVALID_BATCH_STATUS",
            message="当前状态不允许执行该操作",
            status_code=409,
            details=details,
        )


class DataScopeAccessDeniedError(AppException):
    """当前身份无权访问目标数据范围。"""

    def __init__(self, resource_type: str | None = None) -> None:
        super().__init__(
            code="SCOPE_ACCESS_DENIED",
            message="无权访问该数据范围",
            status_code=403,
            details=(
                {"resourceType": resource_type}
                if resource_type is not None
                else None
            ),
        )


class UniqueConflictError(AppException):
    """数据违反唯一性约束。"""

    def __init__(self, field: str | None = None) -> None:
        super().__init__(
            code="UNIQUE_CONFLICT",
            message="数据唯一性冲突",
            status_code=409,
            details={"field": field} if field is not None else None,
        )


class ForeignKeyConflictError(AppException):
    """数据引用的关联记录不存在或不允许被引用。"""

    def __init__(self, field: str | None = None) -> None:
        super().__init__(
            code="FOREIGN_KEY_CONFLICT",
            message="关联数据不存在或外键冲突",
            status_code=409,
            details={"field": field} if field is not None else None,
        )


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
    except IntegrityError as exc:
        response = await integrity_error_handler(request, exc)
    except SQLAlchemyError as exc:
        response = await database_exception_handler(request, exc)
    except Exception:
        # ServerErrorMiddleware 会重新抛出未处理异常，直接在最外层兜底，
        # 才能保证自定义 500 响应和 X-Request-ID 一起返回给客户端。
        logger.exception(
            "未处理的服务端异常 request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
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
    response_headers = dict(headers or {})
    response_headers.setdefault(REQUEST_ID_HEADER, _get_request_id(request))
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body, by_alias=True),
        headers=response_headers,
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


def _integrity_error_state(exc: IntegrityError) -> tuple[str | None, str | None]:
    original = exc.orig
    sqlstate = getattr(original, "sqlstate", None) or getattr(
        original, "pgcode", None
    )
    constraint_name = getattr(original, "constraint_name", None)
    return (
        sqlstate if isinstance(sqlstate, str) else None,
        constraint_name if isinstance(constraint_name, str) else None,
    )


def _map_integrity_error(exc: IntegrityError) -> AppException:
    sqlstate, constraint_name = _integrity_error_state(exc)
    normalized_constraint = (constraint_name or "").lower()
    if sqlstate == "23505" or normalized_constraint.startswith("uq_"):
        return UniqueConflictError()
    if sqlstate == "23503" or normalized_constraint.startswith("fk_"):
        return ForeignKeyConflictError()
    return AppException(
        code="DATABASE_CONSTRAINT_VIOLATION",
        message="数据约束冲突",
        status_code=409,
    )


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """将数据库约束异常转换为稳定的业务错误契约。"""
    return await app_exception_handler(request, _map_integrity_error(exc))


async def database_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """记录不可识别的数据库异常，并隐藏数据库内部细节。"""
    # 交给根日志通道，避免应用运行时被第三方日志配置改变传播链，导致
    # 数据库异常只写入某个孤立 handler，遗漏统一的文件、控制台和采集器。
    logging.getLogger().exception(
        "数据库异常 request_id=%s method=%s path=%s",
        _get_request_id(request),
        request.method,
        request.url.path,
    )
    return _error_response(
        request,
        status_code=500,
        code="DATABASE_ERROR",
        message="数据库服务异常，请稍后重试",
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
    application.add_exception_handler(
        IntegrityError, cast(Any, integrity_error_handler)
    )
    application.add_exception_handler(
        SQLAlchemyError, cast(Any, database_exception_handler)
    )
    application.add_exception_handler(Exception, unhandled_exception_handler)


__all__ = [
    "REQUEST_ID_HEADER",
    "AppException",
    "BatchNotFoundError",
    "DataScopeAccessDeniedError",
    "ForeignKeyConflictError",
    "InsufficientInventoryError",
    "StatusNotAllowedError",
    "UniqueConflictError",
    "app_exception_handler",
    "database_exception_handler",
    "http_exception_handler",
    "integrity_error_handler",
    "register_exception_handlers",
    "request_id_middleware",
    "unhandled_exception_handler",
    "validation_exception_handler",
]
