"""账户管理端点 - 创建、启用、禁用、解锁账户."""

from fastapi import APIRouter, Depends, status

from src.modules.auth.api.dependencies import (
    get_account_service,
    require_admin,
)
from src.modules.auth.api.schemas import (
    ErrorResponse,
    LocalAccountCreateRequest,
    MessageResponse,
    UserResponse,
)
from src.modules.auth.application.services import AccountService

router = APIRouter()


@router.post(
    "/local-accounts",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
async def create_local_account(
    account_data: LocalAccountCreateRequest,
    _: None = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
) -> UserResponse:
    """创建本地账户（仅管理员）.

    异常由全局处理器处理:
    - PasswordTooWeakError → 400
    - InvalidCredentialsError → 401 (用户名/邮箱重复)
    """
    user = await account_service.create_local_account(
        username=account_data.username,
        email=account_data.email,
        password=account_data.password,
        role=account_data.role,
        display_name=account_data.display_name,
    )
    return UserResponse.from_entity(user)


@router.post(
    "/local-accounts/{user_id}/enable",
    response_model=MessageResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def enable_account(
    user_id: int,
    _: None = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
) -> MessageResponse:
    """启用用户账户（仅管理员）.

    异常由全局处理器处理: UserNotFoundError → 404
    """
    await account_service.enable_account(user_id)
    return MessageResponse(message="Account enabled successfully")


@router.post(
    "/local-accounts/{user_id}/disable",
    response_model=MessageResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def disable_account(
    user_id: int,
    _: None = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
) -> MessageResponse:
    """禁用用户账户（仅管理员）.

    异常由全局处理器处理: UserNotFoundError → 404
    """
    await account_service.disable_account(user_id)
    return MessageResponse(message="Account disabled successfully")


@router.post(
    "/local-accounts/{user_id}/unlock",
    response_model=MessageResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def unlock_account(
    user_id: int,
    _: None = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
) -> MessageResponse:
    """解锁被锁定的用户账户（仅管理员）.

    异常由全局处理器处理: UserNotFoundError → 404
    """
    await account_service.unlock_account(user_id)
    return MessageResponse(message="Account unlocked successfully")
