"""通用分页和排序依赖."""

from collections.abc import Sequence
from enum import Enum
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

from src.shared.utils import calculate_total_pages

# =========================================================================
# 分页参数
# =========================================================================

PageParam = Annotated[int, Query(ge=1, description="页码")]
PageSizeParam = Annotated[int, Query(ge=1, le=100, description="每页数量")]


def get_pagination_params(
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
) -> tuple[int, int, int]:
    """获取分页参数. 返回 (page, page_size, offset) 元组."""
    offset = (page - 1) * page_size
    return page, page_size, offset


# =========================================================================
# 排序参数
# =========================================================================


class SortOrder(str, Enum):
    """排序顺序枚举."""

    ASC = "asc"
    DESC = "desc"


SortByParam = Annotated[str, Query(description="排序字段")]
SortOrderParam = Annotated[SortOrder, Query(description="排序顺序 (asc/desc)")]

COMMON_SORT_FIELDS = ["created_at", "updated_at", "name", "id", "status"]


# =========================================================================
# 统一查询参数
# =========================================================================


class ListingParams(BaseModel):
    """统一的列表查询参数。简化服务和端点之间的参数传递。"""

    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"

    @property
    def offset(self) -> int:
        """计算偏移量。"""
        return (self.page - 1) * self.page_size

    def to_dict(self) -> dict:
        """转换为字典，便于解包到仓库方法。"""
        return {
            "page": self.page,
            "page_size": self.page_size,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
        }


def get_listing_params(
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    sort_by: SortByParam = "created_at",
    sort_order: SortOrderParam = SortOrder.DESC,
) -> ListingParams:
    """FastAPI 依赖：获取统一的列表查询参数。

    使用示例:
        @router.get("/items")
        async def list_items(params: ListingParams = Depends(get_listing_params)):
            return await service.list(**params.to_dict())
    """
    return ListingParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )


# =========================================================================
# 分页响应
# =========================================================================

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应基类.

    使用示例:
        class UserListResponse(PaginatedResponse[UserSummary]):
            pass
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


def build_paginated_response(
    items: Sequence[T],
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """构建分页响应字段.

    返回可直接解包到 ListResponse 类的字典:
        return TrainingJobListResponse(**build_paginated_response(...))

    Args:
        items: 当前页的数据项列表
        total: 总记录数
        page: 当前页码
        page_size: 每页数量

    Returns:
        包含 items, total, page, page_size, total_pages 的字典
    """
    return {
        "items": list(items),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calculate_total_pages(total, page_size),
    }
