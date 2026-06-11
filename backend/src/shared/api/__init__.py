"""Shared API - Common API utilities and middleware."""

from .dependencies import OwnedResource, check_resource_ownership
from .exception_handlers import (
    domain_exception_handler,
    problem_exception_handler,
    security_exception_handler,
)
from .pagination import (
    COMMON_SORT_FIELDS,
    ListingParams,
    PageParam,
    PageSizeParam,
    PaginatedResponse,
    SortByParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
    get_listing_params,
    get_pagination_params,
)
from .schemas import EntitySchema

__all__ = [
    "domain_exception_handler",
    "problem_exception_handler",
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
    # 统一查询参数
    "ListingParams",
    "get_listing_params",
    # 资源所有权检查
    "OwnedResource",
    "check_resource_ownership",
]
