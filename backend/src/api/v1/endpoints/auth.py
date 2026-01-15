"""Authentication Endpoints - Login, logout, password management."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import CurrentUser
from src.api.middleware.sso import SSOUserInfo, get_sso_service, map_groups_to_role
from src.api.v1.dependencies import (
    get_account_service,
    get_auth_service,
    get_password_service,
)
from src.api.v1.dependencies.auth import get_current_active_user, require_admin
from src.api.v1.schemas.auth import (
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
from src.application.services.account_service import AccountService
from src.application.services.auth_service import AuthService
from src.application.services.password_service import PasswordService
from src.core.database import get_db
from src.core.security.exceptions import (
    AccountLockedError,
    AuthenticationError,
    InvalidTokenError,
    PasswordExpiredError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
    SSODegradedModeError,
    SSOError,
    TokenExpiredError,
)
from src.domain.value_objects import AuthType, UserRole, UserStatus
from src.infrastructure.persistence.models import UserModel

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    if forwarded := request.headers.get("X-Forwarded-For"):
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _get_or_create_sso_user(
    session: AsyncSession,
    user_info: SSOUserInfo,
    role: str,
) -> UserModel:
    """Get or create SSO user."""
    query_result = await session.execute(
        select(UserModel).where(UserModel.iam_identity_id == user_info.identity_id)
    )
    user = query_result.scalar_one_or_none()

    if not user:
        # Create new SSO user
        user = UserModel(
            username=user_info.username,
            email=user_info.email,
            display_name=user_info.display_name,
            iam_identity_id=user_info.identity_id,
            iam_groups=user_info.groups,
            auth_type=AuthType.SSO,
            status=UserStatus.ACTIVE,
            role=UserRole(role),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        # Update existing user's groups and role
        user.iam_groups = user_info.groups
        user.role = UserRole(role)
        await session.commit()

    return user


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
    session: AsyncSession = Depends(get_db),
):
    """Authenticate user via local credentials or SSO token."""
    auth_service = AuthService(session)
    ip_address = _get_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    try:
        # SSO login
        if login_data.id_token:
            sso_service = get_sso_service()
            if not sso_service:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="SSO is not configured",
                )

            try:
                user_info: SSOUserInfo = await sso_service.validate_id_token(
                    login_data.id_token
                )

                # Map groups to role and create/get user
                role = map_groups_to_role(user_info.groups)

                # Get or create SSO user
                user = await _get_or_create_sso_user(session, user_info, role)

                # Generate tokens using auth_service helper
                tokens = auth_service._create_token_pair(user)

                return LoginResponse(
                    tokens=TokenResponse(
                        access_token=tokens.access_token,
                        refresh_token=tokens.refresh_token,
                        token_type=tokens.token_type,
                        expires_in=tokens.expires_in,
                    ),
                    user=UserResponse(
                        id=user.id,
                        username=user.username,
                        email=user.email,
                        display_name=user.display_name,
                        role=user.role.value,
                        status=user.status.value,
                        auth_type=user.auth_type.value,
                    ),
                )

            except SSODegradedModeError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="SSO service is temporarily unavailable. Please try local login.",
                )
            except SSOError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(e),
                )

        # Local login
        if not login_data.username or not login_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password required for local login",
            )

        result = await auth_service.local_login(
            username=login_data.username,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

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

    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=(
                f"Account is locked until {e.locked_until}"
                if e.locked_until
                else "Account is locked"
            ),
        )
    except PasswordExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password has expired. Please reset your password.",
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
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
    try:
        tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)

        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except (InvalidTokenError, TokenExpiredError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
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
    """Create a new local authentication account (Admin only)."""
    try:
        user = await account_service.create_local_account(
            username=account_data.username,
            email=account_data.email,
            password=account_data.password,
            role=account_data.role,
            display_name=account_data.display_name,
        )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            role=user.role.value,
            status=user.status.value,
            auth_type=user.auth_type.value,
        )
    except PasswordTooWeakError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PASSWORD_TOO_WEAK", "violations": e.violations},
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/local-accounts/{user_id}/enable",
    response_model=MessageResponse,
    responses={403: {"model": ErrorResponse, "description": "Permission denied"}},
)
async def enable_account(
    user_id: int,
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
):
    """Enable a user account (Admin only)."""
    try:
        await account_service.enable_account(user_id)
        return MessageResponse(message="Account enabled successfully")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/local-accounts/{user_id}/disable",
    response_model=MessageResponse,
    responses={403: {"model": ErrorResponse, "description": "Permission denied"}},
)
async def disable_account(
    user_id: int,
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
):
    """Disable a user account (Admin only)."""
    try:
        await account_service.disable_account(user_id)
        return MessageResponse(message="Account disabled successfully")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/local-accounts/{user_id}/unlock",
    response_model=MessageResponse,
    responses={403: {"model": ErrorResponse, "description": "Permission denied"}},
)
async def unlock_account(
    user_id: int,
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
):
    """Unlock a locked user account (Admin only)."""
    try:
        await account_service.unlock_account(user_id)
        return MessageResponse(message="Account unlocked successfully")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


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
    """Change password for the current user."""
    try:
        await password_service.change_password(
            user_id=current_user.user_id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )
        return MessageResponse(message="Password changed successfully")
    except PasswordTooWeakError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PASSWORD_TOO_WEAK", "violations": e.violations},
        )
    except PasswordHistoryViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reuse recent passwords",
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


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
    """Confirm password reset with token."""
    try:
        await password_service.confirm_password_reset(
            reset_token=reset_data.token,
            new_password=reset_data.new_password,
        )
        return MessageResponse(message="Password reset successfully")
    except (InvalidTokenError, TokenExpiredError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token",
        )
    except PasswordTooWeakError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PASSWORD_TOO_WEAK", "violations": e.violations},
        )
    except PasswordHistoryViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reuse recent passwords",
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current user information."""
    result = await session.execute(
        select(UserModel).where(UserModel.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        status=user.status.value,
        auth_type=user.auth_type.value,
    )
