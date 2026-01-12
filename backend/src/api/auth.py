"""Local Account Management API.

Task: T013c - 本地账号管理 API
实现 POST/PUT /auth/local-accounts,支持密码重置和账号启用/禁用,
作为 SSO 不可用时的备用认证,包含密码安全要求
"""

import logging
import re
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

from src.core.config import get_settings
from src.core.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    InvalidCredentialsError,
    PasswordExpiredError,
    PasswordHistoryError,
    ResourceConflictError,
    ResourceNotFoundError,
    TokenError,
)
from src.middleware.auth import CurrentUser, get_current_user, require_role
from src.services.account_service import AccountService, get_account_service
from src.services.password_service import PasswordPolicy, PasswordService, get_password_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Valid roles for the platform
VALID_ROLES = ["admin", "project_manager", "engineer", "viewer"]


def validate_role(role: Optional[str], required: bool = True) -> Optional[str]:
    """Unified role validation for Pydantic models.

    Args:
        role: Role to validate (can be None for optional fields)
        required: Whether role is required

    Returns:
        Validated role or None

    Raises:
        ValueError: If role is invalid or missing when required
    """
    if role is None:
        if required:
            raise ValueError("Role is required")
        return None
    if role not in VALID_ROLES:
        raise ValueError(f"Role must be one of: {VALID_ROLES}")
    return role


def validate_password_field(password: str) -> str:
    """Validate password against policy for Pydantic models.

    Args:
        password: Password to validate

    Returns:
        Validated password

    Raises:
        ValueError: If password doesn't meet policy requirements
    """
    is_valid, violations = PasswordPolicy.validate(password)
    if not is_valid:
        raise ValueError("; ".join(violations))
    return password


# Request/Response models
class LocalAccountCreate(BaseModel):
    """Request to create a local account."""

    username: str
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    role: str = "engineer"

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]{3,64}$", v):
            raise ValueError(
                "Username must be 3-64 characters, alphanumeric with _ and -"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_field(v)

    @field_validator("role")
    @classmethod
    def validate_role_field(cls, v: str) -> str:
        return validate_role(v, required=True)


class LocalAccountUpdate(BaseModel):
    """Request to update a local account."""

    display_name: Optional[str] = None
    role: Optional[str] = None
    is_enabled: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role_field(cls, v: Optional[str]) -> Optional[str]:
        return validate_role(v, required=False)


class PasswordChange(BaseModel):
    """Request to change password."""

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return validate_password_field(v)


class PasswordResetRequest(BaseModel):
    """Request to initiate password reset."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Request to confirm password reset with token."""

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return validate_password_field(v)


class LocalAccountResponse(BaseModel):
    """Response for local account operations."""

    id: int
    username: str
    email: str
    display_name: Optional[str]
    role: str
    is_enabled: bool
    created_at: str
    last_login_at: Optional[str]
    password_expires_at: Optional[str]


class LoginRequest(BaseModel):
    """Login request."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: LocalAccountResponse


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


def _account_to_response(
    account: dict, password_service: PasswordService
) -> LocalAccountResponse:
    """Convert account dict to response model.

    Args:
        account: Account data dictionary
        password_service: Password service for expiry calculation

    Returns:
        LocalAccountResponse model
    """
    password_expires_at = password_service.get_password_expiry_date(
        account["password_changed_at"]
    )
    return LocalAccountResponse(
        id=account["id"],
        username=account["username"],
        email=account["email"],
        display_name=account["display_name"],
        role=account["role"],
        is_enabled=account["is_enabled"],
        created_at=account["created_at"].isoformat(),
        last_login_at=(
            account["last_login_at"].isoformat() if account["last_login_at"] else None
        ),
        password_expires_at=password_expires_at.isoformat(),
    )


@router.post(
    "/local-accounts",
    response_model=LocalAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_local_account(
    account: LocalAccountCreate,
    current_user: Annotated[CurrentUser, Depends(require_role(["admin"]))],
    account_service: Annotated[AccountService, Depends(get_account_service)],
    password_service: Annotated[PasswordService, Depends(get_password_service)],
) -> LocalAccountResponse:
    """Create a new local account (admin only).

    Args:
        account: Account creation request
        current_user: Authenticated admin user
        account_service: Account management service
        password_service: Password management service

    Returns:
        Created account details

    Raises:
        HTTPException: If username or email already exists
    """
    try:
        account_data = account_service.create_account(
            username=account.username,
            email=account.email,
            password=account.password,
            role=account.role,
            display_name=account.display_name,
        )
        logger.info(f"Local account created: {account.username} by {current_user.username}")
        return _account_to_response(account_data, password_service)

    except ResourceConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account creation failed",  # Generic message to avoid enumeration
        )


@router.put("/local-accounts/{username}", response_model=LocalAccountResponse)
async def update_local_account(
    username: str,
    update: LocalAccountUpdate,
    current_user: Annotated[CurrentUser, Depends(require_role(["admin"]))],
    account_service: Annotated[AccountService, Depends(get_account_service)],
    password_service: Annotated[PasswordService, Depends(get_password_service)],
) -> LocalAccountResponse:
    """Update a local account (admin only).

    Args:
        username: Account username
        update: Account update request
        current_user: Authenticated admin user
        account_service: Account management service
        password_service: Password management service

    Returns:
        Updated account details

    Raises:
        HTTPException: If account not found
    """
    try:
        account_data = account_service.update_account(
            username=username,
            display_name=update.display_name,
            role=update.role,
            is_enabled=update.is_enabled,
        )
        logger.info(f"Local account updated: {username} by {current_user.username}")
        return _account_to_response(account_data, password_service)

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    account_service: Annotated[AccountService, Depends(get_account_service)],
    password_service: Annotated[PasswordService, Depends(get_password_service)],
) -> LoginResponse:
    """Authenticate with local account.

    Args:
        credentials: Login credentials
        account_service: Account management service
        password_service: Password management service

    Returns:
        Access token and user info

    Raises:
        HTTPException: If authentication fails
    """
    from src.middleware.auth import create_access_token

    settings = get_settings()

    # Check if local auth is enabled
    if not settings.local_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled",
        )

    try:
        account = account_service.authenticate(
            credentials.username, credentials.password
        )

        # Generate token
        token = create_access_token(
            subject=f"local-{account['id']}",
            username=account["username"],
            email=account["email"],
            role=account["role"],
        )

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=_account_to_response(account, password_service),
        )

    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
        )
    except (InvalidCredentialsError, AccountDisabledError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PasswordExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password expired. Please reset your password.",
        )


@router.post("/password/change", response_model=MessageResponse)
async def change_password(
    request: PasswordChange,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    account_service: Annotated[AccountService, Depends(get_account_service)],
) -> MessageResponse:
    """Change password for current user.

    Args:
        request: Password change request
        current_user: Authenticated user
        account_service: Account management service

    Returns:
        Success message

    Raises:
        HTTPException: If current password is incorrect or new password is in history
    """
    try:
        account_service.change_password(
            username=current_user.username,
            current_password=request.current_password,
            new_password=request.new_password,
        )
        return MessageResponse(message="Password changed successfully")

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    except PasswordHistoryError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post("/password/reset-request", response_model=MessageResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    account_service: Annotated[AccountService, Depends(get_account_service)],
) -> MessageResponse:
    """Request password reset email.

    Args:
        request: Password reset request with email
        account_service: Account management service

    Returns:
        Success message (always returns success to prevent enumeration)
    """
    # Create token (returns None if account doesn't exist)
    token = account_service.create_password_reset_token(request.email)

    if token:
        # TODO: Send email with reset link
        # Security: Never log sensitive tokens in production
        logger.info(f"Password reset requested for email: {request.email}")

    # Always return success to prevent enumeration
    return MessageResponse(
        message="If an account exists with this email, a password reset link has been sent"
    )


@router.post("/password/reset-confirm", response_model=MessageResponse)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    account_service: Annotated[AccountService, Depends(get_account_service)],
) -> MessageResponse:
    """Confirm password reset with token.

    Args:
        request: Password reset confirmation with token and new password
        account_service: Account management service

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        account_service.confirm_password_reset(request.token, request.new_password)
        return MessageResponse(message="Password has been reset successfully")

    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    except PasswordHistoryError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
