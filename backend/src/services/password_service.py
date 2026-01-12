"""Password management service.

Handles password policy validation, hashing, verification,
and password history management.
"""

import logging
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext

from src.core.config import get_settings
from src.core.exceptions import PasswordHistoryError, PasswordValidationError

logger = logging.getLogger(__name__)

# Password hashing context (using bcrypt with cost factor 12)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


class PasswordPolicy:
    """Password policy validation and enforcement."""

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
            violations.append(
                f"Password must be at least {settings.password_min_length} characters"
            )

        if settings.password_require_uppercase and not re.search(r"[A-Z]", password):
            violations.append("Password must contain at least one uppercase letter")

        if settings.password_require_lowercase and not re.search(r"[a-z]", password):
            violations.append("Password must contain at least one lowercase letter")

        if settings.password_require_digit and not re.search(r"\d", password):
            violations.append("Password must contain at least one digit")

        if settings.password_require_special and not re.search(
            r"[!@#$%^&*(),.?\":{}|<>]", password
        ):
            violations.append("Password must contain at least one special character")

        return (len(violations) == 0, violations)

    @staticmethod
    def validate_or_raise(password: str) -> str:
        """Validate password and raise exception if invalid.

        Args:
            password: Password to validate

        Returns:
            Validated password

        Raises:
            PasswordValidationError: If password doesn't meet policy requirements
        """
        is_valid, violations = PasswordPolicy.validate(password)
        if not is_valid:
            raise PasswordValidationError(
                message="; ".join(violations),
                code="PASSWORD_POLICY_VIOLATION",
                details={"violations": violations},
            )
        return password


class PasswordService:
    """Service for password operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return _pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Stored hash

        Returns:
            True if password matches
        """
        return _pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_reset_token() -> str:
        """Generate secure password reset token.

        Returns:
            URL-safe token string
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def check_password_history(
        new_password: str,
        password_history: list[str],
        history_count: Optional[int] = None,
    ) -> None:
        """Check if new password is in recent history.

        Args:
            new_password: New password to check
            password_history: List of previous password hashes
            history_count: Number of recent passwords to check (defaults to config)

        Raises:
            PasswordHistoryError: If password matches recent history
        """
        if not password_history:
            return

        settings = get_settings()
        count = history_count or settings.password_history_count

        for old_hash in password_history[-count:]:
            if _pwd_context.verify(new_password, old_hash):
                raise PasswordHistoryError(
                    message=f"Cannot reuse one of your last {count} passwords",
                    code="PASSWORD_HISTORY_VIOLATION",
                )

    @staticmethod
    def is_password_expired(password_changed_at: datetime) -> bool:
        """Check if password has expired.

        Args:
            password_changed_at: When password was last changed

        Returns:
            True if password is expired
        """
        settings = get_settings()
        password_age = datetime.utcnow() - password_changed_at
        return password_age.days > settings.password_expire_days

    @staticmethod
    def get_password_expiry_date(password_changed_at: datetime) -> datetime:
        """Get password expiration date.

        Args:
            password_changed_at: When password was last changed

        Returns:
            Password expiration datetime
        """
        settings = get_settings()
        return password_changed_at + timedelta(days=settings.password_expire_days)


# Singleton instance
_password_service: Optional[PasswordService] = None


def get_password_service() -> PasswordService:
    """Get or create password service singleton.

    Returns:
        PasswordService instance
    """
    global _password_service
    if _password_service is None:
        _password_service = PasswordService()
    return _password_service
