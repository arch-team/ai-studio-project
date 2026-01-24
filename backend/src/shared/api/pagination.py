"""通用分页依赖和工具."""

from typing import Annotated

from fastapi import Query

# 分页参数类型别名 - 不包含默认值
PageParam = Annotated[int, Query(ge=1, description="页码")]
PageSizeParam = Annotated[int, Query(ge=1, le=100, description="每页数量")]


def get_pagination_params(
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
) -> tuple[int, int, int]:
    """
    获取分页参数.

    返回: (page, page_size, offset) 元组
    """
    offset = (page - 1) * page_size
    return page, page_size, offset