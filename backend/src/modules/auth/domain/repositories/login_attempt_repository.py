"""LoginAttempt Repository Interface - Data access contract for login attempts."""

from abc import ABC, abstractmethod

from ..entities import LoginAttempt


class ILoginAttemptRepository(ABC):
    """Abstract repository interface for LoginAttempt entity."""

    @abstractmethod
    async def create(self, attempt: LoginAttempt) -> LoginAttempt:
        """Create a new login attempt record."""

    @abstractmethod
    async def get_recent_failures(
        self, username: str, limit: int = 5
    ) -> list[LoginAttempt]:
        """Get recent failed login attempts for a username."""
