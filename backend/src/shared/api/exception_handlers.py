"""Global Exception Handlers - Centralized exception to HTTP response mapping.

设计说明:
---------
异常处理器直接从异常类读取 http_status 和 error_code 属性，
无需维护映射表。新增异常只需在异常类中定义这两个属性即可。

响应格式 (统一):
--------------
{
    "error": {
        "code": "ERROR_CODE",
        "message": "错误消息",
        "details": {...},       # 可选，结构化错误详情
        "trace_id": "req-xxx"   # 可选，请求追踪 ID
    }
}

设计参考:
--------
- 简化版 RFC 9457 (Problem Details)
- Google Cloud API 风格
- 前端 AppError.fromApiResponse() 兼容
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from src.shared.domain.exceptions import DomainError
from src.shared.infrastructure.security.exceptions import SecurityError


def _get_trace_id(request: Request) -> str | None:
    """从请求中提取 trace_id。"""
    return getattr(request.state, "trace_id", None)


def _get_domain_error_details(exc: DomainError) -> dict[str, Any] | None:
    """提取 Domain 异常的结构化详情。"""
    # 调用异常的 get_details() 方法（如果存在）
    if hasattr(exc, "get_details") and callable(exc.get_details):
        return exc.get_details()
    return None


def _get_security_error_details(exc: SecurityError) -> dict[str, Any] | None:
    """提取 Security 异常的结构化详情。"""
    details: dict[str, Any] = {}

    if hasattr(exc, "locked_until") and exc.locked_until:
        details["locked_until"] = exc.locked_until
    if hasattr(exc, "violations"):
        details["violations"] = exc.violations
    if hasattr(exc, "required_permission"):
        details["required_permission"] = exc.required_permission
    if hasattr(exc, "user_id"):
        details["user_id"] = exc.user_id

    return details if details else None


def _build_error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """构建统一的错误响应格式。"""
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if details:
        error["details"] = details
    if trace_id:
        error["trace_id"] = trace_id

    return {"error": error}


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Handle all Domain layer exceptions.

    直接从异常类读取 http_status 和 error_code 属性。
    """
    return JSONResponse(
        status_code=exc.http_status,
        content=_build_error_response(
            code=exc.error_code,
            message=exc.message,
            details=_get_domain_error_details(exc),
            trace_id=_get_trace_id(request),
        ),
    )


async def security_exception_handler(
    request: Request, exc: SecurityError
) -> JSONResponse:
    """Handle all Security layer exceptions.

    直接从异常类读取 http_status 属性。
    """
    return JSONResponse(
        status_code=exc.http_status,
        content=_build_error_response(
            code=exc.code,
            message=exc.message,
            details=_get_security_error_details(exc),
            trace_id=_get_trace_id(request),
        ),
    )
