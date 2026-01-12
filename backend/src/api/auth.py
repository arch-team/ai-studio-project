"""Local Account Management API.

Task: T013c - 本地账号管理 API
实现 POST/PUT /auth/local-accounts,支持密码重置和账号启用/禁用,
作为 SSO 不可用时的备用认证,包含密码安全要求
"""

import logging
import re
import secrets
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from passlib.context import CryptContext

from src.core.config import get_settings
from src.middleware.auth import CurrentUser, get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Password hashing context (using bcrypt with cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


class PasswordPolicy:
    """Password policy validation."""

    @staticmethod
    def validate(password: str) -> tuple[bool, list[str]]:
        """Validate password against policy.

        Args:
            password: Plain text password

        Returns:
            Tuple of (is_valid, list of violation messages)
        """
        settings = get_settings()
        violations = []

        if len(password) < settings.password_min_length:
            violations.append(f"Password must be at least {settings.password_min_length} characters")

        if settings.password_require_uppercase and not re.search(r"[A-Z]", password):
            violations.append("Password must contain at least one uppercase letter")

        if settings.password_require_lowercase and not re.search(r"[a-z]", password):
            violations.append("Password must contain at least one lowercase letter")

        if settings.password_require_digit and not re.search(r"\d", password):
            violations.append("Password must contain at least one digit")

        if settings.password_require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            violations.append("Password must contain at least one special character")

        return (len(violations) == 0, violations)


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
            raise ValueError("Username must be 3-64 characters, alphanumeric with _ and -")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        is_valid, violations = PasswordPolicy.validate(v)
        if not is_valid:
            raise ValueError("; ".join(violations))
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["admin", "project_manager", "engineer", "viewer"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {valid_roles}")
        return v


class LocalAccountUpdate(BaseModel):
    """Request to update a local account."""

    display_name: Optional[str] = None
    role: Optional[str] = None
    is_enabled: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_roles = ["admin", "project_manager", "engineer", "viewer"]
            if v not in valid_roles:
                raise ValueError(f"Role must be one of: {valid_roles}")
        return v


class PasswordChange(BaseModel):
    """Request to change password."""

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        is_valid, violations = PasswordPolicy.validate(v)
        if not is_valid:
            raise ValueError("; ".join(violations))
        return v


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
        is_valid, violations = PasswordPolicy.validate(v)
        if not is_valid:
            raise ValueError("; ".join(violations))
        return v


class LocalAccountResponse(BaseModel):
    """Response for local account operations."""

    id: int
    username: str
    email: str
    display_name: Optional[str]
    role: str
    is_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    password_expires_at: Optional[datetime]


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


# In-memory stores (replace with database in production)
# These are placeholders - actual implementation will use SQLAlchemy models
_local_accounts: dict[str, dict] = {}
_password_reset_tokens: dict[str, tuple[str, datetime]] = {}  # token -> (email, expiry)
_login_attempts: dict[str, list[datetime]] = {}  # username -> list of attempt times


def hash_password(password: str) -> str:
    """Hash password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash.

    Args:
        plain_password: Plain text password
        hashed_password: Stored hash

    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def check_login_lockout(username: str) -> bool:
    """Check if account is locked due to failed attempts.

    Args:
        username: Account username

    Returns:
        True if account is locked
    """
    settings = get_settings()
    attempts = _login_attempts.get(username, [])

    # Filter recent attempts within lockout window
    lockout_start = datetime.utcnow() - timedelta(minutes=settings.login_lockout_minutes)
    recent_attempts = [a for a in attempts if a > lockout_start]

    return len(recent_attempts) >= settings.login_max_attempts


def record_login_attempt(username: str, success: bool) -> None:
    """Record login attempt for lockout tracking.

    Args:
        username: Account username
        success: Whether login was successful
    """
    if success:
        # Clear attempts on successful login
        _login_attempts.pop(username, None)
    else:
        # Record failed attempt
        if username not in _login_attempts:
            _login_attempts[username] = []
        _login_attempts[username].append(datetime.utcnow())


def generate_reset_token() -> str:
    """Generate secure password reset token.

    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(32)


@router.post(
    "/local-accounts",
    response_model=LocalAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_local_account(
    account: LocalAccountCreate,
    current_user: Annotated[CurrentUser, Depends(require_role(["admin"]))],
) -> LocalAccountResponse:
    """Create a new local account (admin only).

    Args:
        account: Account creation request
        current_user: Authenticated admin user

    Returns:
        Created account details

    Raises:
        HTTPException: If username or email already exists
    """
    # Check for existing account
    if account.username in _local_accounts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account creation failed",  # Generic message to avoid enumeration
        )

    # Check email uniqueness
    for existing in _local_accounts.values():
        if existing["email"] == account.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account creation failed",
            )

    settings = get_settings()
    now = datetime.utcnow()

    # Create account
    account_data = {
        "id": len(_local_accounts) + 1,
        "username": account.username,
        "email": account.email,
        "password_hash": hash_password(account.password),
        "display_name": account.display_name,
        "role": account.role,
        "is_enabled": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
        "password_changed_at": now,
        "password_history": [hash_password(account.password)],
    }

    _local_accounts[account.username] = account_data

    logger.info(f"Local account created: {account.username} by {current_user.username}")

    return LocalAccountResponse(
        id=account_data["id"],
        username=account_data["username"],
        email=account_data["email"],
        display_name=account_data["display_name"],
        role=account_data["role"],
        is_enabled=account_data["is_enabled"],
        created_at=account_data["created_at"],
        last_login_at=account_data["last_login_at"],
        password_expires_at=now + timedelta(days=settings.password_expire_days),
    )


@router.put("/local-accounts/{username}", response_model=LocalAccountResponse)
async def update_local_account(
    username: str,
    update: LocalAccountUpdate,
    current_user: Annotated[CurrentUser, Depends(require_role(["admin"]))],
) -> LocalAccountResponse:
    """Update a local account (admin only).

    Args:
        username: Account username
        update: Account update request
        current_user: Authenticated admin user

    Returns:
        Updated account details

    Raises:
        HTTPException: If account not found
    """
    if username not in _local_accounts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    account = _local_accounts[username]
    settings = get_settings()

    # Apply updates
    if update.display_name is not None:
        account["display_name"] = update.display_name
    if update.role is not None:
        account["role"] = update.role
    if update.is_enabled is not None:
        account["is_enabled"] = update.is_enabled

    account["updated_at"] = datetime.utcnow()

    logger.info(f"Local account updated: {username} by {current_user.username}")

    return LocalAccountResponse(
        id=account["id"],
        username=account["username"],
        email=account["email"],
        display_name=account["display_name"],
        role=account["role"],
        is_enabled=account["is_enabled"],
        created_at=account["created_at"],
        last_login_at=account["last_login_at"],
        password_expires_at=account["password_changed_at"] + timedelta(days=settings.password_expire_days),
    )


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest) -> LoginResponse:
    """Authenticate with local account.

    Args:
        credentials: Login credentials

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

    # Check lockout
    if check_login_lockout(credentials.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked. Try again in {settings.login_lockout_minutes} minutes",
        )

    # Generic error for invalid credentials (avoid enumeration)
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check account exists
    account = _local_accounts.get(credentials.username)
    if not account:
        record_login_attempt(credentials.username, False)
        raise auth_error

    # Check account is enabled
    if not account.get("is_enabled", True):
        record_login_attempt(credentials.username, False)
        raise auth_error

    # Verify password
    if not verify_password(credentials.password, account["password_hash"]):
        record_login_attempt(credentials.username, False)
        raise auth_error

    # Check password expiration
    password_age = datetime.utcnow() - account["password_changed_at"]
    if password_age.days > settings.password_expire_days:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password expired. Please reset your password.",
        )

    # Successful login
    record_login_attempt(credentials.username, True)
    account["last_login_at"] = datetime.utcnow()

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
        user=LocalAccountResponse(
            id=account["id"],
            username=account["username"],
            email=account["email"],
            display_name=account["display_name"],
            role=account["role"],
            is_enabled=account["is_enabled"],
            created_at=account["created_at"],
            last_login_at=account["last_login_at"],
            password_expires_at=account["password_changed_at"] + timedelta(days=settings.password_expire_days),
        ),
    )


@router.post("/password/change", response_model=MessageResponse)
async def change_password(
    request: PasswordChange,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> MessageResponse:
    """Change password for current user.

    Args:
        request: Password change request
        current_user: Authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If current password is incorrect or new password is in history
    """
    settings = get_settings()

    # Find account by username
    account = _local_accounts.get(current_user.username)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Verify current password
    if not verify_password(request.current_password, account["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Check password history
    new_hash = hash_password(request.new_password)
    for old_hash in account.get("password_history", [])[-settings.password_history_count:]:
        if verify_password(request.new_password, old_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reuse one of your last {settings.password_history_count} passwords",
            )

    # Update password
    account["password_hash"] = new_hash
    account["password_changed_at"] = datetime.utcnow()
    account["password_history"].append(new_hash)

    logger.info(f"Password changed for user: {current_user.username}")

    return MessageResponse(message="Password changed successfully")


@router.post("/password/reset-request", response_model=MessageResponse)
async def request_password_reset(request: PasswordResetRequest) -> MessageResponse:
    """Request password reset email.

    Args:
        request: Password reset request with email

    Returns:
        Success message (always returns success to prevent enumeration)
    """
    # Find account by email (don't reveal if exists)
    account = None
    for acc in _local_accounts.values():
        if acc["email"] == request.email:
            account = acc
            break

    if account:
        # Generate token
        token = generate_reset_token()
        expiry = datetime.utcnow() + timedelta(minutes=15)
        _password_reset_tokens[token] = (request.email, expiry)

        # TODO: Send email with reset link
        # For now, log the token (remove in production!)
        logger.info(f"Password reset token generated for {request.email}: {token}")

    # Always return success to prevent enumeration
    return MessageResponse(
        message="If an account exists with this email, a password reset link has been sent"
    )


@router.post("/password/reset-confirm", response_model=MessageResponse)
async def confirm_password_reset(request: PasswordResetConfirm) -> MessageResponse:
    """Confirm password reset with token.

    Args:
        request: Password reset confirmation with token and new password

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid or expired
    """
    settings = get_settings()

    # Validate token
    token_data = _password_reset_tokens.get(request.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    email, expiry = token_data
    if datetime.utcnow() > expiry:
        del _password_reset_tokens[request.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Find account
    account = None
    for acc in _local_accounts.values():
        if acc["email"] == email:
            account = acc
            break

    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check password history
    for old_hash in account.get("password_history", [])[-settings.password_history_count:]:
        if verify_password(request.new_password, old_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reuse one of your last {settings.password_history_count} passwords",
            )

    # Update password
    new_hash = hash_password(request.new_password)
    account["password_hash"] = new_hash
    account["password_changed_at"] = datetime.utcnow()
    account["password_history"].append(new_hash)

    # Invalidate token
    del _password_reset_tokens[request.token]

    logger.info(f"Password reset completed for: {email}")

    return MessageResponse(message="Password has been reset successfully")
