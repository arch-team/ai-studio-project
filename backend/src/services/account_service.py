"""Local account management service.

Handles account CRUD operations, login tracking, and lockout management.
This is a temporary in-memory implementation; production will use database.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from src.core.config import get_settings
from src.core.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    InvalidCredentialsError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from src.core.singleton import create_singleton_getter
from src.services.password_service import PasswordService, get_password_service

logger = logging.getLogger(__name__)


# In-memory stores (replace with database in production)
# These are placeholders - actual implementation will use SQLAlchemy models
_account_storage: dict[str, dict] = {}
_password_reset_tokens: dict[str, tuple[str, datetime]] = {}  # token -> (email, expiry)
_login_attempts: dict[str, list[datetime]] = {}  # username -> list of attempt times


class AccountService:
    """Service for local account management."""

    def __init__(self, password_service: Optional[PasswordService] = None) -> None:
        """Initialize account service.

        Args:
            password_service: Optional password service instance
        """
        self._password_service = password_service or get_password_service()

    def find_by_username(self, username: str) -> Optional[dict]:
        """Find account by username.

        Args:
            username: Account username

        Returns:
            Account dict if found, None otherwise
        """
        return _account_storage.get(username)

    def find_by_email(self, email: str) -> Optional[dict]:
        """Find account by email address.

        Args:
            email: Email address to search for

        Returns:
            Account dict if found, None otherwise
        """
        for account in _account_storage.values():
            if account["email"] == email:
                return account
        return None

    def create_account(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "engineer",
        display_name: Optional[str] = None,
    ) -> dict:
        """Create a new local account.

        Args:
            username: Account username
            email: Email address
            password: Plain text password (will be hashed)
            role: User role
            display_name: Optional display name

        Returns:
            Created account data

        Raises:
            ResourceConflictError: If username or email already exists
        """
        if username in _account_storage:
            raise ResourceConflictError(
                message="Account creation failed",
                code="ACCOUNT_EXISTS",
            )

        if self.find_by_email(email):
            raise ResourceConflictError(
                message="Account creation failed",
                code="EMAIL_EXISTS",
            )

        now = datetime.utcnow()
        password_hash = self._password_service.hash_password(password)

        account_data = {
            "id": len(_account_storage) + 1,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "display_name": display_name,
            "role": role,
            "is_enabled": True,
            "created_at": now,
            "updated_at": now,
            "last_login_at": None,
            "password_changed_at": now,
            "password_history": [password_hash],
        }

        _account_storage[username] = account_data
        logger.info(f"Local account created: {username}")

        return account_data

    def update_account(
        self,
        username: str,
        display_name: Optional[str] = None,
        role: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> dict:
        """Update account details.

        Args:
            username: Account username
            display_name: New display name
            role: New role
            is_enabled: New enabled status

        Returns:
            Updated account data

        Raises:
            ResourceNotFoundError: If account not found
        """
        account = _account_storage.get(username)
        if not account:
            raise ResourceNotFoundError(
                message="Account not found",
                code="ACCOUNT_NOT_FOUND",
            )

        if display_name is not None:
            account["display_name"] = display_name
        if role is not None:
            account["role"] = role
        if is_enabled is not None:
            account["is_enabled"] = is_enabled

        account["updated_at"] = datetime.utcnow()
        logger.info(f"Local account updated: {username}")

        return account

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change account password.

        Args:
            username: Account username
            current_password: Current password for verification
            new_password: New password

        Raises:
            ResourceNotFoundError: If account not found
            InvalidCredentialsError: If current password is incorrect
            PasswordHistoryError: If new password matches recent history
        """
        account = _account_storage.get(username)
        if not account:
            raise ResourceNotFoundError(
                message="Account not found",
                code="ACCOUNT_NOT_FOUND",
            )

        if not self._password_service.verify_password(
            current_password, account["password_hash"]
        ):
            raise InvalidCredentialsError(
                message="Current password is incorrect",
                code="INVALID_CURRENT_PASSWORD",
            )

        # Check password history (raises PasswordHistoryError if match)
        self._password_service.check_password_history(
            new_password, account.get("password_history", [])
        )

        # Update password
        new_hash = self._password_service.hash_password(new_password)
        account["password_hash"] = new_hash
        account["password_changed_at"] = datetime.utcnow()
        account["password_history"].append(new_hash)

        logger.info(f"Password changed for user: {username}")

    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts.

        Args:
            username: Account username

        Returns:
            True if account is locked
        """
        settings = get_settings()
        attempts = _login_attempts.get(username, [])

        # Filter recent attempts within lockout window
        lockout_start = datetime.utcnow() - timedelta(
            minutes=settings.login_lockout_minutes
        )
        recent_attempts = [a for a in attempts if a > lockout_start]

        return len(recent_attempts) >= settings.login_max_attempts

    def record_login_attempt(self, username: str, success: bool) -> None:
        """Record login attempt for lockout tracking.

        Args:
            username: Account username
            success: Whether login was successful
        """
        if success:
            _login_attempts.pop(username, None)
        else:
            if username not in _login_attempts:
                _login_attempts[username] = []
            _login_attempts[username].append(datetime.utcnow())

    def authenticate(self, username: str, password: str) -> dict:
        """Authenticate user with username and password.

        Args:
            username: Account username
            password: Plain text password

        Returns:
            Account data if authentication successful

        Raises:
            AccountLockedError: If account is locked
            InvalidCredentialsError: If credentials are invalid
            AccountDisabledError: If account is disabled
            PasswordExpiredError: If password is expired
        """
        # Check lockout first
        if self.is_account_locked(username):
            settings = get_settings()
            raise AccountLockedError(
                message=f"Account temporarily locked. Try again in {settings.login_lockout_minutes} minutes",
                code="ACCOUNT_LOCKED",
            )

        # Find account
        account = _account_storage.get(username)
        if not account:
            self.record_login_attempt(username, False)
            raise InvalidCredentialsError(
                message="Invalid credentials",
                code="INVALID_CREDENTIALS",
            )

        # Check enabled
        if not account.get("is_enabled", True):
            self.record_login_attempt(username, False)
            raise AccountDisabledError(
                message="Account is disabled",
                code="ACCOUNT_DISABLED",
            )

        # Verify password
        if not self._password_service.verify_password(
            password, account["password_hash"]
        ):
            self.record_login_attempt(username, False)
            raise InvalidCredentialsError(
                message="Invalid credentials",
                code="INVALID_CREDENTIALS",
            )

        # Check password expiration
        if self._password_service.is_password_expired(account["password_changed_at"]):
            from src.core.exceptions import PasswordExpiredError

            raise PasswordExpiredError(
                message="Password expired. Please reset your password.",
                code="PASSWORD_EXPIRED",
            )

        # Success
        self.record_login_attempt(username, True)
        account["last_login_at"] = datetime.utcnow()

        return account

    def create_password_reset_token(self, email: str) -> Optional[str]:
        """Create password reset token for account.

        Args:
            email: Account email

        Returns:
            Reset token if account exists, None otherwise
        """
        account = self.find_by_email(email)
        if not account:
            return None

        token = self._password_service.generate_reset_token()
        expiry = datetime.utcnow() + timedelta(minutes=15)
        _password_reset_tokens[token] = (email, expiry)

        logger.info(f"Password reset requested for email: {email}")
        return token

    def confirm_password_reset(self, token: str, new_password: str) -> None:
        """Confirm password reset with token.

        Args:
            token: Reset token
            new_password: New password

        Raises:
            PasswordResetTokenError: If token is invalid or expired
            PasswordHistoryError: If new password matches recent history
        """
        from src.core.exceptions import PasswordResetTokenError

        token_data = _password_reset_tokens.get(token)
        if not token_data:
            raise PasswordResetTokenError(
                message="Invalid or expired reset token",
                code="INVALID_TOKEN",
            )

        email, expiry = token_data
        if datetime.utcnow() > expiry:
            del _password_reset_tokens[token]
            raise PasswordResetTokenError(
                message="Invalid or expired reset token",
                code="TOKEN_EXPIRED",
            )

        account = self.find_by_email(email)
        if not account:
            raise PasswordResetTokenError(
                message="Invalid or expired reset token",
                code="ACCOUNT_NOT_FOUND",
            )

        # Check password history
        self._password_service.check_password_history(
            new_password, account.get("password_history", [])
        )

        # Update password
        new_hash = self._password_service.hash_password(new_password)
        account["password_hash"] = new_hash
        account["password_changed_at"] = datetime.utcnow()
        account["password_history"].append(new_hash)

        # Invalidate token
        del _password_reset_tokens[token]

        logger.info(f"Password reset completed for: {email}")


# Singleton instance - 使用通用单例工厂
get_account_service = create_singleton_getter(AccountService)
