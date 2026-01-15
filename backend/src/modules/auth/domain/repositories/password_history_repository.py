"""PasswordHistory Repository Interface - Data access contract for password history."""

from abc import ABC, abstractmethod

from ..entities import PasswordHistory


class IPasswordHistoryRepository(ABC):
    """Abstract repository interface for PasswordHistory entity."""

    @abstractmethod
    async def create(self, history: PasswordHistory) -> PasswordHistory:
        """Create a new password history entry."""

    @abstractmethod
    async def get_recent(self, user_id: int, limit: int = 5) -> list[PasswordHistory]:
        """Get recent password history entries for a user."""

    @abstractmethod
    async def cleanup_old_entries(self, user_id: int, keep_count: int = 5) -> int:
        """Remove old password history entries, keeping only the most recent ones.

        Returns:
            Number of entries deleted.
        """
