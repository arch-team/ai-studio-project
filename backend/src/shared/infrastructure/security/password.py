"""Password Hashing and Validation - Security-compliant password management."""

import re

import bcrypt

from src.shared.infrastructure.security.constants import (
    PASSWORD_BCRYPT_COST,
    PASSWORD_HISTORY_COUNT,
    PASSWORD_MIN_LENGTH,
)


class PasswordHasher:
    """Password hashing using bcrypt."""

    # bcrypt 只处理密码的前 72 字节，bcrypt>=4.1 起超长密码会直接抛 ValueError，
    # 故在 hash/verify 两端都先截断，避免线上超长密码请求 500。
    _BCRYPT_MAX_BYTES = 72

    def __init__(self, cost_factor: int = PASSWORD_BCRYPT_COST):
        self._cost_factor = cost_factor

    def _encode(self, password: str) -> bytes:
        """将密码编码并截断到 bcrypt 的 72 字节上限（按字节边界安全截断）。"""
        return password.encode("utf-8")[: self._BCRYPT_MAX_BYTES]

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(
            self._encode(password),
            bcrypt.gensalt(rounds=self._cost_factor),
        ).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        try:
            return bcrypt.checkpw(
                self._encode(plain_password),
                hashed_password.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False

    def needs_rehash(self, hashed_password: str) -> bool:
        """Check if a password hash needs to be updated (cost factor changed)."""
        try:
            # 从哈希中提取 rounds: $2b$12$...
            parts = hashed_password.split("$")
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds != self._cost_factor
        except (ValueError, IndexError):
            pass
        return True


class PasswordValidator:
    """Password strength validation following enterprise security standards."""

    @staticmethod
    def validate_strength(password: str) -> list[str]:
        """Validate password strength per FR-015 requirements."""
        violations = []

        if len(password) < PASSWORD_MIN_LENGTH:
            violations.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")

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
        password_history: list[str],
        hasher: PasswordHasher,
    ) -> bool:
        """Check if password was recently used (True if OK, False if reused)."""
        recent_history = password_history[:PASSWORD_HISTORY_COUNT]
        return not any(hasher.verify_password(new_password, old_hash) for old_hash in recent_history)


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
