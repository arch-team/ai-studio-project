"""用户管理端点 - 用户 CRUD API (T055, T056, T057)."""

from fastapi import APIRouter, Depends, status

from src.shared.api.pagination import (
    PageParam,
    PageSizeParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
)

from ...application.services import UserService
from ...domain.value_objects import UserRole, UserStatus
from ..dependencies import get_user_service, require_admin
from ..schemas import (
    CreateUserRequest,
    ErrorResponse,
    UpdateUserRequest,
    UserDetailResponse,
    UserListResponse,
    UserRoleEnum,
    UserStatusEnum,
    UserSummaryResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=UserListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
async def list_users(
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    role: UserRoleEnum | None = None,
    status_filter: UserStatusEnum | None = None,
    sort_by: str = "created_at",
    sort_order: SortOrderParam = SortOrder.DESC,
    _: None = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserListResponse:
    """获取用户列表（仅管理员）.

    支持分页、角色和状态过滤、排序。
    """
    # Convert enum to domain value objects
    role_filter = UserRole(role.value) if role else None
    status_vo = UserStatus(status_filter.value) if status_filter else None

    users, total = await user_service.list_users(
        page=page,
        page_size=page_size,
        role=role_filter,
        status=status_vo,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )

    items = [UserSummaryResponse.from_entity(user) for user in users]
    return UserListResponse(**build_paginated_response(items, total, page, page_size))


@router.post(
    "",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        409: {"model": ErrorResponse, "description": "User already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def create_user(
    data: CreateUserRequest,
    _: None = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    """创建用户（仅管理员）.

    创建 SSO 用户（无密码）。如需创建本地账户，请使用 /local-accounts 端点。
    """
    user = await user_service.create_user(
        username=data.username,
        email=data.email,
        role=data.role.value,
        display_name=data.display_name,
        resource_quota_id=data.resource_quota_id,
    )
    return UserDetailResponse.from_entity(user)


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
        422: {"model": ErrorResponse, "description": "Invalid ID format"},
    },
)
async def get_user(
    user_id: int,
    _: None = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    """获取用户详情（仅管理员）."""
    user = await user_service.get_user(user_id)
    return UserDetailResponse.from_entity(user)


@router.put(
    "/{user_id}",
    response_model=UserDetailResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def update_user(
    user_id: int,
    data: UpdateUserRequest,
    _: None = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    """更新用户（仅管理员）.

    可更新用户角色、状态、显示名称和资源配额。
    """
    user = await user_service.update_user(
        user_id=user_id,
        role=data.role.value if data.role else None,
        status=data.status.value if data.status else None,
        display_name=data.display_name,
        resource_quota_id=data.resource_quota_id,
    )
    return UserDetailResponse.from_entity(user)
