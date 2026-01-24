"""Shared API - Common API utilities and middleware."""

from .exception_handlers import (
    DOMAIN_EXCEPTION_MAP,
    SECURITY_EXCEPTION_MAP,
    domain_exception_handler,
    security_exception_handler,
)
from .pagination import (
    COMMON_SORT_FIELDS,
    PageParam,
    PageSizeParam,
    PaginatedResponse,
    SortByParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
    get_pagination_params,
)
from .schemas import EntitySchema

__all__ = [
    "DOMAIN_EXCEPTION_MAP",
    "SECURITY_EXCEPTION_MAP",
    "domain_exception_handler",
    "security_exception_handler",
    "EntitySchema",
    # 分页
    "PageParam",
    "PageSizeParam",
    "get_pagination_params",
    # 排序
    "SortByParam",
    "SortOrder",
    "SortOrderParam",
    "COMMON_SORT_FIELDS",
    # 分页响应
    "PaginatedResponse",
    "build_paginated_response",
]
