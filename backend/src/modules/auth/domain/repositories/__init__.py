"""Auth domain repository interfaces."""

from .login_attempt_repository import ILoginAttemptRepository
from .password_history_repository import IPasswordHistoryRepository
from .user_repository import IUserRepository

__all__ = [
    "IUserRepository",
    "ILoginAttemptRepository",
    "IPasswordHistoryRepository",
]
