"""Authentication Service - Core authentication logic for local and SSO accounts."""

from dataclasses import dataclass
from datetime import timedelta

from src.shared.infrastructure.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    LOCKOUT_DURATION_MINUTES,
    MAX_FAILED_LOGIN_ATTEMPTS,
    JWTManager,
    PasswordHasher,
    TokenType,
    get_jwt_manager,
    get_password_hasher,
)
from src.shared.utils import utc_now

from ...domain.entities import LoginAttempt, User
from ...domain.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    PasswordExpiredError,
)
from ...domain.repositories import ILoginAttemptRepository, IUserRepository
from ...domain.value_objects import AuthType, UserStatus


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
    """Authentication service for login and token management."""

    def __init__(
        self,
        user_repository: IUserRepository,
        login_attempt_repository: ILoginAttemptRepository,
        jwt_manager: JWTManager | None = None,
        password_hasher: PasswordHasher | None = None,
    ):
        self._user_repository = user_repository
        self._login_attempt_repository = login_attempt_repository
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
        user = await self._user_repository.get_by_username(username)

        # Create login attempt record (initially failed)
        attempt = LoginAttempt(
            id=None,
            user_id=user.id if user else None,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason=None,
        )

        try:
            if not user:
                attempt.failure_reason = "user_not_found"
                raise InvalidCredentialsError("Invalid credentials")

            if user.auth_type != AuthType.LOCAL:
                attempt.failure_reason = "not_local_account"
                raise InvalidCredentialsError("This account uses SSO authentication")

            if user.status != UserStatus.ACTIVE:
                attempt.failure_reason = "account_inactive"
                raise InvalidCredentialsError("Account is not active")

            if user.is_locked():
                attempt.failure_reason = "account_locked"
                raise AccountLockedError(locked_until=(user.locked_until.isoformat() if user.locked_until else None))

            if not user.password_hash or not self._hasher.verify_password(password, user.password_hash):
                await self._handle_failed_login(user)
                attempt.failure_reason = "invalid_password"
                raise InvalidCredentialsError("Invalid credentials")

            if user.is_password_expired():
                attempt.failure_reason = "password_expired"
                raise PasswordExpiredError()

            # Login successful
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
            # Always record the login attempt
            await self._login_attempt_repository.create(attempt)

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """Refresh access token using refresh token."""
        payload = self._jwt.verify_token(refresh_token, TokenType.REFRESH)
        user_id = int(payload.sub)

        user = await self._user_repository.get_by_id(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise InvalidCredentialsError("User not found or inactive")

        return self._create_token_pair(user)

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        return await self._user_repository.get_by_id(user_id)

    def create_token_pair_for_user(self, user: User) -> TokenPair:
        """Create token pair for a user (used for SSO login)."""
        return self._create_token_pair(user)

    def _create_token_pair(self, user: User) -> TokenPair:
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

    async def _handle_failed_login(self, user: User) -> None:
        """Handle failed login attempt."""
        user.record_failed_login()

        if user.failed_login_count >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.lock_account(utc_now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES))

        await self._user_repository.update(user)

    async def _handle_successful_login(self, user: User) -> None:
        """Handle successful login."""
        user.reset_login_failures()
        user.record_login()
        await self._user_repository.update(user)
