"""Authentication Endpoints - Login, logout, password management."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..application.services import AccountService, AuthService, PasswordService
from ..application.services.auth_service import TokenPair
from ..domain.entities import User
from .current_user import CurrentUser
from .dependencies import (
    get_account_service,
    get_auth_service,
    get_current_active_user,
    get_password_service,
    require_admin,
)
from .schemas import (
    ErrorResponse,
    LocalAccountCreateRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    if forwarded := request.headers.get("X-Forwarded-For"):
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _create_user_response(user: User) -> UserResponse:
    """Create UserResponse from User entity."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        status=user.status.value,
        auth_type=user.auth_type.value,
    )


def _create_login_response(user: User, tokens: TokenPair) -> LoginResponse:
    """Create LoginResponse from User entity and TokenPair."""
    return LoginResponse(
        tokens=TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        ),
        user=_create_user_response(user),
    )


def _create_fallback_login_response(result) -> LoginResponse:
    """创建向后兼容的登录响应（当无法获取完整用户信息时）"""
    return LoginResponse(
        tokens=TokenResponse(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            token_type=result.tokens.token_type,
            expires_in=result.tokens.expires_in,
        ),
        user=UserResponse(
            id=result.user_id,
            username=result.username,
            email=result.email,
            display_name=None,
            role=result.role,
            status="active",
            auth_type="local",
        ),
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        423: {"model": ErrorResponse, "description": "Account locked"},
    },
)
async def login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    account_service: AccountService = Depends(get_account_service),
):
    """Authenticate user via local credentials or SSO token.

    Exceptions are handled by global exception handlers:
    - AccountLockedError → 423
    - PasswordExpiredError → 401
    - InvalidCredentialsError → 401
    - SSOError → 401
    - SSODegradedModeError → 503
    """
    # SSO login
    if login_data.id_token:
        return await _handle_sso_login(
            login_data.id_token, auth_service, account_service
        )

    # Local login
    return await _handle_local_login(request, login_data, auth_service)


async def _handle_local_login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService,
) -> LoginResponse:
    """处理本地账户登录

    Args:
        request: FastAPI 请求对象
        login_data: 登录请求数据
        auth_service: 认证服务

    Returns:
        LoginResponse: 登录响应

    Raises:
        HTTPException: 缺少用户名或密码
    """
    if not login_data.username or not login_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password required for local login",
        )

    ip_address = _get_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    result = await auth_service.local_login(
        username=login_data.username,
        password=login_data.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Get full user for response
    user = await auth_service.get_user_by_id(result.user_id)
    if user:
        return _create_login_response(user, result.tokens)

    # Fallback for backward compatibility
    return _create_fallback_login_response(result)


async def _handle_sso_login(
    id_token: str,
    auth_service: AuthService,
    account_service: AccountService,
) -> LoginResponse:
    """Handle SSO login flow.

    Raises:
        HTTPException: If SSO is not configured
        SSOError: If token validation fails (handled by global handler)
        SSODegradedModeError: If SSO service unavailable (handled by global handler)
    """
    sso_service = _get_sso_service_or_raise()

    # Validate token and get user info
    user_info = await sso_service.validate_id_token(id_token)

    # Get or create SSO user
    user = await _get_or_create_sso_user(account_service, user_info)

    # Generate tokens
    tokens = auth_service.create_token_pair_for_user(user)
    return _create_login_response(user, tokens)


def _get_sso_service_or_raise():
    """获取 SSO 服务实例，未配置时抛出异常"""
    try:
        from src.api.middleware.sso import get_sso_service

        sso_service = get_sso_service()
        if not sso_service:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="SSO is not configured",
            )
        return sso_service
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SSO is not configured",
        )


async def _get_or_create_sso_user(account_service: AccountService, user_info):
    """根据 SSO 用户信息获取或创建用户"""
    from src.api.middleware.sso import map_groups_to_role

    role = map_groups_to_role(user_info.groups)
    return await account_service.get_or_create_sso_user(
        iam_identity_id=user_info.identity_id,
        username=user_info.username,
        email=user_info.email,
        display_name=user_info.display_name,
        groups=user_info.groups,
        role=role,
    )


@router.post(
    "/token/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse, "description": "Invalid token"}},
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """Logout current user."""
    # In a stateless JWT system, logout is handled client-side by discarding tokens
    # For enhanced security, implement token blacklisting in Redis
    return MessageResponse(message="Logged out successfully")


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
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
):
    """Create a new local authentication account (Admin only).

    Exceptions handled by global handler:
    - PasswordTooWeakError → 400
    - InvalidCredentialsError → 401 (for duplicate username/email)
    """
    user = await account_service.create_local_account(
        username=account_data.username,
        email=account_data.email,
        password=account_data.password,
        role=account_data.role,
        display_name=account_data.display_name,
    )
    return _create_user_response(user)


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
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
):
    """Enable a user account (Admin only).

    Exceptions handled by global handler: UserNotFoundError → 404
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
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
):
    """Disable a user account (Admin only).

    Exceptions handled by global handler: UserNotFoundError → 404
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
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
):
    """Unlock a locked user account (Admin only).

    Exceptions handled by global handler: UserNotFoundError → 404
    """
    await account_service.unlock_account(user_id)
    return MessageResponse(message="Account unlocked successfully")


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
    """Change password for the current user.

    Exceptions handled by global handler:
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
    """Request a password reset email."""
    # Token would be used in production to send email with reset link
    _ = await password_service.request_password_reset(reset_data.email)

    # Note: In production, send email with reset link containing the token
    # For now, we just acknowledge the request
    # Don't reveal if user exists for security reasons
    return MessageResponse(
        message="If an account exists with this email, a password reset link will be sent"
    )


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
    """Confirm password reset with token.

    Exceptions handled by global handler:
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current user information."""
    user = await auth_service.get_user_by_id(current_user.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return _create_user_response(user)
