"""通用分页和排序依赖."""

from enum import Enum
from typing import Annotated

from fastapi import Query


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


# 预定义的常用排序字段选项 (用于文档和验证提示)
COMMON_SORT_FIELDS = ["created_at", "updated_at", "name", "id", "status"]