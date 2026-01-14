"""Authentication Service - Core authentication logic for local and SSO accounts."""

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security.constants import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    LOCKOUT_DURATION_MINUTES,
    MAX_FAILED_LOGIN_ATTEMPTS,
    PASSWORD_EXPIRY_DAYS,
    PASSWORD_HISTORY_COUNT,
)
from src.core.security.exceptions import (
    AccountLockedError,
    AuthenticationError,
    PasswordExpiredError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
)
from src.core.security.jwt import JWTManager, TokenType, get_jwt_manager
from src.core.security.password import (
    PasswordHasher,
    PasswordValidator,
    get_password_hasher,
    get_password_validator,
)
from src.core.utils import utc_now
from src.infrastructure.persistence.models import (
    AuthType,
    LoginAttemptModel,
    PasswordHistoryModel,
    UserModel,
    UserStatus,
)
from src.infrastructure.persistence.models.user_model import UserRole


@dataclass
class TokenPair:
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0


@dataclass
class AuthResult:
    """Authentication result with user info and tokens."""

    user_id: int
    username: str
    email: str
    role: str
    tokens: TokenPair


class AuthService:
    """Authentication service for login, logout, and password management."""

    def __init__(
        self,
        session: AsyncSession,
        jwt_manager: JWTManager | None = None,
        password_hasher: PasswordHasher | None = None,
        password_validator: PasswordValidator | None = None,
    ):
        self._session = session
        self._jwt = jwt_manager or get_jwt_manager()
        self._hasher = password_hasher or get_password_hasher()
        self._validator = password_validator or get_password_validator()

    async def local_login(
        self,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str | None = None,
    ) -> AuthResult:
        """Authenticate with username and password."""
        user = await self._get_user_by_username(username)

        attempt = LoginAttemptModel(
            user_id=user.id if user else None,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
        )

        try:
            if not user:
                attempt.failure_reason = "user_not_found"
                raise AuthenticationError("Invalid credentials")

            if user.auth_type != AuthType.LOCAL:
                attempt.failure_reason = "not_local_account"
                raise AuthenticationError("This account uses SSO authentication")

            if user.status != UserStatus.ACTIVE:
                attempt.failure_reason = "account_inactive"
                raise AuthenticationError("Account is not active")

            if user.is_locked():
                attempt.failure_reason = "account_locked"
                raise AccountLockedError(
                    locked_until=(
                        user.locked_until.isoformat() if user.locked_until else None
                    )
                )

            # Verify password
            if not user.password_hash or not self._hasher.verify_password(
                password, user.password_hash
            ):
                await self._handle_failed_login(user)
                attempt.failure_reason = "invalid_password"
                raise AuthenticationError("Invalid credentials")

            # Check password expiry
            if user.is_password_expired():
                attempt.failure_reason = "password_expired"
                raise PasswordExpiredError()

            # Successful login
            attempt.success = True
            await self._handle_successful_login(user)

            # Generate tokens
            tokens = self._create_token_pair(user)

            return AuthResult(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role.value,
                tokens=tokens,
            )

        finally:
            self._session.add(attempt)
            await self._session.commit()

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """Refresh access token using refresh token."""
        payload = self._jwt.verify_token(refresh_token, TokenType.REFRESH)
        user_id = int(payload.sub)

        user = await self._get_user_by_id(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise AuthenticationError("User not found or inactive")

        return self._create_token_pair(user)

    async def create_local_account(
        self,
        username: str,
        email: str,
        password: str,
        role: str,
        display_name: str | None = None,
    ) -> UserModel:
        """Create a new local authentication account."""
        # Validate password strength
        violations = self._validator.validate_strength(password)
        if violations:
            raise PasswordTooWeakError(violations)

        # Check username uniqueness
        existing = await self._get_user_by_username(username)
        if existing:
            raise AuthenticationError("Username already exists")

        # Check email uniqueness
        existing_email = await self._get_user_by_email(email)
        if existing_email:
            raise AuthenticationError("Email already exists")

        # Hash password
        password_hash = self._hasher.hash_password(password)

        # Create user
        user = UserModel(
            username=username,
            email=email,
            display_name=display_name,
            password_hash=password_hash,
            password_expires_at=utc_now() + timedelta(days=PASSWORD_EXPIRY_DAYS),
            auth_type=AuthType.LOCAL,
            status=UserStatus.ACTIVE,
            role=UserRole(role),
        )
        self._session.add(user)
        await self._session.flush()

        # Record password in history
        history = PasswordHistoryModel(
            user_id=user.id,
            password_hash=password_hash,
        )
        self._session.add(history)
        await self._session.commit()

        return user

    async def _validate_new_password(self, user_id: int, new_password: str) -> None:
        """Validate password strength and check history."""
        violations = self._validator.validate_strength(new_password)
        if violations:
            raise PasswordTooWeakError(violations)

        password_history = await self._get_password_history(user_id)
        history_hashes = [h.password_hash for h in password_history]

        if not self._validator.check_password_history(
            new_password, history_hashes, self._hasher
        ):
            raise PasswordHistoryViolationError()

    async def _update_user_password(self, user: UserModel, new_password: str) -> None:
        """Update user password and add to history."""
        new_hash = self._hasher.hash_password(new_password)
        user.password_hash = new_hash
        user.password_expires_at = utc_now() + timedelta(days=PASSWORD_EXPIRY_DAYS)
        user.failed_login_count = 0
        user.locked_until = None

        history = PasswordHistoryModel(
            user_id=user.id,
            password_hash=new_hash,
        )
        self._session.add(history)
        await self._cleanup_password_history(user.id)

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change user password."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        if not user.is_local_account():
            raise AuthenticationError("Cannot change password for SSO account")

        if not user.password_hash or not self._hasher.verify_password(
            current_password, user.password_hash
        ):
            raise AuthenticationError("Current password is incorrect")

        await self._validate_new_password(user_id, new_password)
        await self._update_user_password(user, new_password)
        await self._session.commit()

    async def request_password_reset(self, email: str) -> str | None:
        """Request password reset and return reset token."""
        user = await self._get_user_by_email(email)
        if not user or not user.is_local_account():
            # Don't reveal if user exists
            return None

        if user.status != UserStatus.ACTIVE:
            return None

        # Generate reset token
        return self._jwt.create_password_reset_token(user.id, user.email)

    async def confirm_password_reset(
        self,
        reset_token: str,
        new_password: str,
    ) -> None:
        """Confirm password reset with token."""
        payload = self._jwt.verify_token(reset_token, TokenType.PASSWORD_RESET)
        user_id = int(payload.sub)

        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        if not user.is_local_account():
            raise AuthenticationError("Cannot reset password for SSO account")

        await self._validate_new_password(user_id, new_password)
        await self._update_user_password(user, new_password)
        await self._session.commit()

    async def enable_account(self, user_id: int) -> None:
        """Enable a user account."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        user.status = UserStatus.ACTIVE
        user.locked_until = None
        user.failed_login_count = 0
        await self._session.commit()

    async def disable_account(self, user_id: int) -> None:
        """Disable a user account."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        user.status = UserStatus.INACTIVE
        await self._session.commit()

    async def unlock_account(self, user_id: int) -> None:
        """Unlock a locked user account."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        user.locked_until = None
        user.failed_login_count = 0
        await self._session.commit()

    def _create_token_pair(self, user: UserModel) -> TokenPair:
        """Create access and refresh token pair."""
        access_token = self._jwt.create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
        )
        refresh_token = self._jwt.create_refresh_token(user_id=user.id)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def _handle_failed_login(self, user: UserModel) -> None:
        """Handle failed login attempt."""
        user.failed_login_count += 1

        if user.failed_login_count >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = utc_now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

        await self._session.commit()

    async def _handle_successful_login(self, user: UserModel) -> None:
        """Handle successful login."""
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = utc_now()
        await self._session.commit()

    async def _get_user_by_username(self, username: str) -> UserModel | None:
        """Get user by username."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        return result.scalar_one_or_none()

    async def _get_user_by_email(self, email: str) -> UserModel | None:
        """Get user by email."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: int) -> UserModel | None:
        """Get user by ID."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_password_history(self, user_id: int) -> list[PasswordHistoryModel]:
        """Get password history for user."""
        result = await self._session.execute(
            select(PasswordHistoryModel)
            .where(PasswordHistoryModel.user_id == user_id)
            .order_by(PasswordHistoryModel.created_at.desc())
            .limit(PASSWORD_HISTORY_COUNT)
        )
        return list(result.scalars().all())

    async def _cleanup_password_history(self, user_id: int) -> None:
        """Keep only the most recent PASSWORD_HISTORY_COUNT entries."""
        # Get all history entries
        result = await self._session.execute(
            select(PasswordHistoryModel)
            .where(PasswordHistoryModel.user_id == user_id)
            .order_by(PasswordHistoryModel.created_at.desc())
        )
        history = list(result.scalars().all())

        # Delete old entries beyond the limit
        if len(history) > PASSWORD_HISTORY_COUNT:
            for entry in history[PASSWORD_HISTORY_COUNT:]:
                await self._session.delete(entry)
