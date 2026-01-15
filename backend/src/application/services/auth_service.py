"""Authentication Service - Core authentication logic for local and SSO accounts."""

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.mixins import UserQueryMixin
from src.core.security.constants import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    LOCKOUT_DURATION_MINUTES,
    MAX_FAILED_LOGIN_ATTEMPTS,
)
from src.core.security.exceptions import (
    AccountLockedError,
    AuthenticationError,
    PasswordExpiredError,
)
from src.core.security.jwt import JWTManager, TokenType, get_jwt_manager
from src.core.security.password import PasswordHasher, get_password_hasher
from src.core.utils import utc_now
from src.domain.value_objects import AuthType, UserStatus
from src.infrastructure.persistence.models import LoginAttemptModel, UserModel


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


class AuthService(UserQueryMixin):
    """Authentication service for login and token management."""

    def __init__(
        self,
        session: AsyncSession,
        jwt_manager: JWTManager | None = None,
        password_hasher: PasswordHasher | None = None,
    ):
        self._session = session
        self._jwt = jwt_manager or get_jwt_manager()
        self._hasher = password_hasher or get_password_hasher()

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

            if not user.password_hash or not self._hasher.verify_password(
                password, user.password_hash
            ):
                await self._handle_failed_login(user)
                attempt.failure_reason = "invalid_password"
                raise AuthenticationError("Invalid credentials")

            if user.is_password_expired():
                attempt.failure_reason = "password_expired"
                raise PasswordExpiredError()

            attempt.success = True
            await self._handle_successful_login(user)

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
