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

    def _check_user_login_eligibility(self, user: User | None, password: str) -> str | None:
        """检查用户登录资格。返回 failure_reason（None 表示通过）。"""
        if not user:
            return "user_not_found"
        if user.auth_type != AuthType.LOCAL:
            return "not_local_account"
        if user.status != UserStatus.ACTIVE:
            return "account_inactive"
        if user.is_locked():
            return "account_locked"
        if not user.password_hash or not self._hasher.verify_password(password, user.password_hash):
            return "invalid_password"
        if user.is_password_expired():
            return "password_expired"
        return None

    def _raise_login_error(self, reason: str, user: User | None) -> None:
        """根据失败原因抛出对应异常。"""
        error_map = {
            "user_not_found": lambda: InvalidCredentialsError("Invalid credentials"),
            "not_local_account": lambda: InvalidCredentialsError("This account uses SSO authentication"),
            "account_inactive": lambda: InvalidCredentialsError("Account is not active"),
            "account_locked": lambda: AccountLockedError(
                locked_until=(user.locked_until.isoformat() if user and user.locked_until else None)
            ),
            "invalid_password": lambda: InvalidCredentialsError("Invalid credentials"),
            "password_expired": lambda: PasswordExpiredError(),
        }
        raise error_map.get(reason, lambda: InvalidCredentialsError("Unknown error"))()

    def _build_auth_result(self, user: User) -> AuthResult:
        """构建认证结果。"""
        assert user.id is not None, "User must have ID after authentication"
        return AuthResult(
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            tokens=self._create_token_pair(user),
        )

    async def local_login(
        self,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str | None = None,
    ) -> AuthResult:
        """使用用户名和密码进行本地认证。"""
        user = await self._user_repository.get_by_username(username)
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
            failure_reason = self._check_user_login_eligibility(user, password)
            if failure_reason:
                attempt.failure_reason = failure_reason
                if failure_reason == "invalid_password" and user:
                    await self._handle_failed_login(user)
                self._raise_login_error(failure_reason, user)

            attempt.success = True
            await self._handle_successful_login(user)  # type: ignore
            return self._build_auth_result(user)  # type: ignore
        finally:
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

    def _create_token_pair(self, user: User) -> TokenPair:
        """创建访问令牌和刷新令牌对（内部使用和 SSO 登录）。"""
        if user.id is None:
            raise ValueError("User must have ID to create tokens")
        return TokenPair(
            access_token=self._jwt.create_access_token(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role.value,
            ),
            refresh_token=self._jwt.create_refresh_token(user_id=user.id),
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # 向后兼容的别名
    create_token_pair_for_user = _create_token_pair

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
