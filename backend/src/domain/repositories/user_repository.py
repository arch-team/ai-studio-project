"""User Repository Interface - Data access contract for users."""

from abc import ABC, abstractmethod

from src.domain.entities.user import User


class IUserRepository(ABC):
    """Abstract repository interface for User entity."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user."""

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if a user with the given username exists."""

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email exists."""
