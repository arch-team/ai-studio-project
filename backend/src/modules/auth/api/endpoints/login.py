"""登录相关端点 - 登录、登出、Token 管理、用户信息."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import (
    get_account_service,
    get_auth_service,
    get_current_active_user,
)
from src.modules.auth.api.schemas import (
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from src.modules.auth.application.services import AccountService, AuthService
from src.modules.auth.application.services.auth_service import TokenPair
from src.modules.auth.domain.entities import User

router = APIRouter()


# =========================================================================
# 辅助函数
# =========================================================================


def _get_client_ip(request: Request) -> str:
    """从请求中提取客户端 IP."""
    if forwarded := request.headers.get("X-Forwarded-For"):
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _create_user_response(user: User) -> UserResponse:
    """从 User 实体创建 UserResponse."""
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
    """从 User 实体和 TokenPair 创建 LoginResponse."""
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
    """创建向后兼容的登录响应（当无法获取完整用户信息时）."""
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


# =========================================================================
# 登录端点
# =========================================================================


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
    """用户登录（本地凭证或 SSO Token）.

    异常由全局处理器处理:
    - AccountLockedError → 423
    - PasswordExpiredError → 401
    - InvalidCredentialsError → 401
    - SSOError → 401
    - SSODegradedModeError → 503
    """
    # SSO 登录
    if login_data.id_token:
        return await _handle_sso_login(
            login_data.id_token, auth_service, account_service
        )

    # 本地登录
    return await _handle_local_login(request, login_data, auth_service)


async def _handle_local_login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService,
) -> LoginResponse:
    """处理本地账户登录."""
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

    # 获取完整用户信息
    user = await auth_service.get_user_by_id(result.user_id)
    if user:
        return _create_login_response(user, result.tokens)

    # 向后兼容
    return _create_fallback_login_response(result)


async def _handle_sso_login(
    id_token: str,
    auth_service: AuthService,
    account_service: AccountService,
) -> LoginResponse:
    """处理 SSO 登录流程."""
    sso_service = _get_sso_service_or_raise()

    # 验证 Token 并获取用户信息
    user_info = await sso_service.validate_id_token(id_token)

    # 获取或创建 SSO 用户
    user = await _get_or_create_sso_user(account_service, user_info)

    # 生成 Token
    tokens = auth_service.create_token_pair_for_user(user)
    return _create_login_response(user, tokens)


def _get_sso_service_or_raise():
    """获取 SSO 服务实例，未配置时抛出异常."""
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
    """根据 SSO 用户信息获取或创建用户."""
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


# =========================================================================
# Token 管理端点
# =========================================================================


@router.post(
    "/token/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse, "description": "Invalid token"}},
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """使用 Refresh Token 刷新 Access Token."""
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
    """登出当前用户."""
    # 无状态 JWT 系统中，登出由客户端丢弃 Token 处理
    # 增强安全性可在 Redis 中实现 Token 黑名单
    return MessageResponse(message="Logged out successfully")


# =========================================================================
# 用户信息端点
# =========================================================================


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """获取当前用户信息."""
    user = await auth_service.get_user_by_id(current_user.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return _create_user_response(user)
