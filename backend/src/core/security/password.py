"""Password Hashing and Validation - Security-compliant password management."""

import re
from typing import List

from passlib.context import CryptContext

from src.core.security.constants import (
    PASSWORD_BCRYPT_COST,
    PASSWORD_HISTORY_COUNT,
    PASSWORD_MIN_LENGTH,
)


class PasswordHasher:
    """Password hashing using bcrypt."""

    def __init__(self, cost_factor: int = PASSWORD_BCRYPT_COST):
        self._context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=cost_factor,
        )

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self._context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return self._context.verify(plain_password, hashed_password)

    def needs_rehash(self, hashed_password: str) -> bool:
        """Check if a password hash needs to be updated."""
        return self._context.needs_update(hashed_password)


class PasswordValidator:
    """Password strength validation following enterprise security standards."""

    @staticmethod
    def validate_strength(password: str) -> List[str]:
        """Validate password strength, return list of violations.

        Requirements (FR-015):
        - Minimum 12 characters
        - At least one lowercase letter
        - At least one uppercase letter
        - At least one digit
        - At least one special character
        """
        violations = []

        if len(password) < PASSWORD_MIN_LENGTH:
            violations.append(
                f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
            )

        if not re.search(r"[a-z]", password):
            violations.append("Password must contain at least one lowercase letter")

        if not re.search(r"[A-Z]", password):
            violations.append("Password must contain at least one uppercase letter")

        if not re.search(r"\d", password):
            violations.append("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;\'`~]', password):
            violations.append("Password must contain at least one special character")

        return violations

    @staticmethod
    def check_password_history(
        new_password: str,
        password_history: List[str],
        hasher: PasswordHasher,
    ) -> bool:
        """Check if password was recently used.

        Returns True if password is OK (not in history), False if it was recently used.
        """
        # Only check the most recent N passwords
        recent_history = password_history[:PASSWORD_HISTORY_COUNT]

        for old_hash in recent_history:
            if hasher.verify_password(new_password, old_hash):
                return False

        return True


# Singleton instance for convenience
_password_hasher: PasswordHasher | None = None


def get_password_hasher() -> PasswordHasher:
    """Get or create password hasher singleton."""
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = PasswordHasher()
    return _password_hasher


def get_password_validator() -> PasswordValidator:
    """Get password validator (stateless, can create new instance)."""
    return PasswordValidator()
