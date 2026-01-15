"""Audit API request schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogQueryParams(BaseModel):
    """Query parameters for audit log list."""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    user_id: int | None = Field(default=None, description="用户ID过滤")
    resource_type: str | None = Field(default=None, description="资源类型过滤")
    resource_id: str | None = Field(default=None, description="资源ID过滤")
    operation_type: str | None = Field(default=None, description="操作类型过滤")
    start_date: datetime | None = Field(default=None, description="开始日期")
    end_date: datetime | None = Field(default=None, description="结束日期")
