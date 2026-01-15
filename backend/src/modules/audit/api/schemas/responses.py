"""Audit API response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Response schema for audit log."""

    id: int = Field(description="审计日志ID")
    operation_type: str = Field(description="操作类型")
    resource_type: str = Field(description="资源类型")
    status: str = Field(description="操作状态")
    user_id: int | None = Field(description="用户ID")
    resource_id: str | None = Field(description="资源ID")
    request_data: dict[str, Any] | None = Field(description="请求数据")
    response_data: dict[str, Any] | None = Field(description="响应数据")
    ip_address: str | None = Field(description="IP地址")
    user_agent: str | None = Field(description="User-Agent")
    created_at: datetime = Field(description="创建时间")
    expires_at: datetime = Field(description="过期时间")

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response schema for audit log list."""

    items: list[AuditLogResponse] = Field(description="审计日志列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")


class AuditLogCountResponse(BaseModel):
    """Response schema for audit log count."""

    count: int = Field(description="审计日志数量")


class CleanupResultResponse(BaseModel):
    """Response schema for cleanup operation result."""

    deleted_count: int = Field(description="删除的记录数")
    message: str = Field(description="操作结果消息")
