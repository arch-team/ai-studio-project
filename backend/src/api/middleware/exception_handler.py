"""全局异常处理器

统一处理应用中的异常,返回标准化的错误响应
"""

import logging
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.schemas.common import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理请求验证异常

    Args:
        request: 请求对象
        exc: 验证异常

    Returns:
        JSONResponse: 标准化错误响应
    """
    errors = exc.errors()
    error_details = []

    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"])
        error_details.append(
            ErrorDetail(
                code="VALIDATION_ERROR",
                message=error["msg"],
                field=field,
            ).model_dump()
        )

    # 如果只有一个错误,返回简化格式
    if len(error_details) == 1:
        response_data = ErrorResponse(
            success=False,
            error=ErrorDetail(**error_details[0]),
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None,
        )
    else:
        # 多个错误,返回完整列表
        response_data = {
            "success": False,
            "errors": error_details,
            "request_id": (
                request.state.request_id if hasattr(request.state, "request_id") else None
            ),
        }

    logger.warning(f"请求验证失败: {request.url} - {error_details}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data.model_dump() if isinstance(response_data, ErrorResponse) else response_data,
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """处理数据库异常

    Args:
        request: 请求对象
        exc: 数据库异常

    Returns:
        JSONResponse: 标准化错误响应
    """
    logger.error(f"数据库错误: {request.url} - {str(exc)}", exc_info=True)

    # 检查是否是完整性约束违反
    if isinstance(exc, IntegrityError):
        error_code = "DATABASE_INTEGRITY_ERROR"
        error_message = "数据完整性约束违反,可能存在重复或无效的数据"
    else:
        error_code = "DATABASE_ERROR"
        error_message = "数据库操作失败"

    response_data = ErrorResponse(
        success=False,
        error=ErrorDetail(code=error_code, message=error_message),
        request_id=request.state.request_id if hasattr(request.state, "request_id") else None,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data.model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理通用异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSONResponse: 标准化错误响应
    """
    logger.error(f"未处理的异常: {request.url} - {str(exc)}", exc_info=True)

    response_data = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="服务器内部错误",
        ),
        request_id=request.state.request_id if hasattr(request.state, "request_id") else None,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data.model_dump(),
    )


def register_exception_handlers(app: Any) -> None:
    """注册异常处理器到FastAPI应用

    Args:
        app: FastAPI应用实例
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("异常处理器注册完成")


__all__ = [
    "validation_exception_handler",
    "database_exception_handler",
    "general_exception_handler",
    "register_exception_handlers",
]
