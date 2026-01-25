"""密码管理端点 - 修改密码、重置密码."""

from fastapi import APIRouter, Depends

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import (
    get_current_active_user,
    get_password_service,
)
from src.modules.auth.api.schemas import (
    ErrorResponse,
    MessageResponse,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
)
from src.modules.auth.application.services import PasswordService

router = APIRouter()


@router.post(
    "/password/change",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
    },
)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: CurrentUser = Depends(get_current_active_user),
    password_service: PasswordService = Depends(get_password_service),
):
    """修改当前用户密码.

    异常由全局处理器处理:
    - PasswordTooWeakError → 400
    - PasswordHistoryViolationError → 400
    - InvalidCredentialsError → 401
    """
    await password_service.change_password(
        user_id=current_user.user_id,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )
    return MessageResponse(message="Password changed successfully")


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    password_service: PasswordService = Depends(get_password_service),
):
    """请求密码重置邮件."""
    # Token 在生产环境用于发送包含重置链接的邮件
    _ = await password_service.request_password_reset(reset_data.email)

    # 注意: 生产环境应发送包含 Token 的重置链接邮件
    # 目前仅确认请求，出于安全考虑不透露用户是否存在
    return MessageResponse(message="If an account exists with this email, a password reset link will be sent")


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Invalid token"},
    },
)
async def confirm_password_reset(
    reset_data: PasswordResetConfirmRequest,
    password_service: PasswordService = Depends(get_password_service),
):
    """使用 Token 确认密码重置.

    异常由全局处理器处理:
    - InvalidTokenError → 401
    - TokenExpiredError → 401
    - PasswordTooWeakError → 400
    - PasswordHistoryViolationError → 400
    - InvalidCredentialsError → 401
    """
    await password_service.confirm_password_reset(
        reset_token=reset_data.token,
        new_password=reset_data.new_password,
    )
    return MessageResponse(message="Password reset successfully")
