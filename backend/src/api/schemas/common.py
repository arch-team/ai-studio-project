"""通用API响应模型"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """错误详情"""

    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    field: str | None = Field(None, description="相关字段")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "VALIDATION_ERROR",
                    "message": "用户名长度必须在3-50个字符之间",
                    "field": "username",
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """错误响应"""

    success: bool = Field(default=False, description="请求是否成功")
    error: ErrorDetail = Field(..., description="错误详情")
    request_id: str | None = Field(None, description="请求ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "用户名或密码错误",
                    },
                    "request_id": "req-123456",
                }
            ]
        }
    }


class SuccessResponse(BaseModel, Generic[T]):
    """成功响应"""

    success: bool = Field(default=True, description="请求是否成功")
    data: T = Field(..., description="响应数据")
    request_id: str | None = Field(None, description="请求ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": {"id": 1, "name": "示例数据"},
                    "request_id": "req-123456",
                }
            ]
        }
    }


class PaginationMeta(BaseModel):
    """分页元数据"""

    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, le=100, description="每页大小")
    total: int = Field(..., ge=0, description="总记录数")
    total_pages: int = Field(..., ge=0, description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page": 1,
                    "page_size": 20,
                    "total": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False,
                }
            ]
        }
    }


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""

    success: bool = Field(default=True, description="请求是否成功")
    data: list[T] = Field(..., description="数据列表")
    pagination: PaginationMeta = Field(..., description="分页元数据")
    request_id: str | None = Field(None, description="请求ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": [{"id": 1, "name": "示例1"}, {"id": 2, "name": "示例2"}],
                    "pagination": {
                        "page": 1,
                        "page_size": 20,
                        "total": 100,
                        "total_pages": 5,
                        "has_next": True,
                        "has_prev": False,
                    },
                    "request_id": "req-123456",
                }
            ]
        }
    }


__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "SuccessResponse",
    "PaginationMeta",
    "PaginatedResponse",
]
