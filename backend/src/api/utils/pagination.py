"""分页工具

提供统一的分页逻辑和辅助函数
"""

import math
from typing import Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.common import PaginatedResponse, PaginationMeta

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页参数"""

    page: int = Field(default=1, ge=1, description="页码(从1开始)")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小(1-100)")

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """获取限制数"""
        return self.page_size


def get_pagination_params(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
) -> PaginationParams:
    """获取分页参数(用于FastAPI依赖注入)

    Args:
        page: 页码
        page_size: 每页大小

    Returns:
        PaginationParams: 分页参数对象
    """
    return PaginationParams(page=page, page_size=page_size)


async def paginate(
    db: AsyncSession,
    query: Select[tuple[T]],
    params: PaginationParams,
) -> tuple[list[T], PaginationMeta]:
    """执行分页查询

    Args:
        db: 数据库会话
        query: SQLAlchemy查询对象
        params: 分页参数

    Returns:
        tuple: (数据列表, 分页元数据)
    """
    # 查询总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar_one()

    # 计算总页数
    total_pages = math.ceil(total / params.page_size) if total > 0 else 0

    # 执行分页查询
    paginated_query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(paginated_query)
    items = list(result.scalars().all())

    # 创建分页元数据
    pagination = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_prev=params.page > 1,
    )

    return items, pagination


def create_paginated_response(
    data: list[T],
    pagination: PaginationMeta,
    request_id: str | None = None,
) -> PaginatedResponse[T]:
    """创建分页响应

    Args:
        data: 数据列表
        pagination: 分页元数据
        request_id: 请求ID

    Returns:
        PaginatedResponse: 分页响应对象
    """
    return PaginatedResponse(
        success=True,
        data=data,
        pagination=pagination,
        request_id=request_id,
    )


__all__ = [
    "PaginationParams",
    "get_pagination_params",
    "paginate",
    "create_paginated_response",
]
