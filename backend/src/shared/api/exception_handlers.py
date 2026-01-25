"""Global Exception Handlers - Centralized exception to HTTP response mapping.

设计说明:
---------
所有异常现在都继承自 Problem 基类，通过 @problem 装饰器注入 http_status 和 error_code，
get_details() 自动返回所有数据字段。

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
from src.shared.domain.problem import Problem
from src.shared.infrastructure.security.exceptions import SecurityError


def _get_trace_id(request: Request) -> str | None:
    """从请求中提取 trace_id。"""
    return getattr(request.state, "trace_id", None)


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

    所有 Domain 异常现在继承自 Problem，使用 error_code 和 get_details()。
    """
    return JSONResponse(
        status_code=exc.http_status,
        content=_build_error_response(
            code=exc.error_code,
            message=exc.message,
            details=exc.get_details(),
            trace_id=_get_trace_id(request),
        ),
    )


async def security_exception_handler(request: Request, exc: SecurityError) -> JSONResponse:
    """Handle all Security layer exceptions.

    所有 Security 异常现在继承自 Problem，使用 error_code 和 get_details()。
    """
    return JSONResponse(
        status_code=exc.http_status,
        content=_build_error_response(
            code=exc.error_code,
            message=exc.message,
            details=exc.get_details(),
            trace_id=_get_trace_id(request),
        ),
    )


async def problem_exception_handler(request: Request, exc: Problem) -> JSONResponse:
    """Handle all Problem-based exceptions.

    Problem 基类使用装饰器注入 http_status 和 error_code，
    get_details() 自动返回所有数据字段。

    响应格式与 DomainError/SecurityError 保持一致，前端无需修改。
    """
    return JSONResponse(
        status_code=exc.http_status,
        content=_build_error_response(
            code=exc.error_code,
            message=exc.message,
            details=exc.get_details(),
            trace_id=_get_trace_id(request),
        ),
    )
