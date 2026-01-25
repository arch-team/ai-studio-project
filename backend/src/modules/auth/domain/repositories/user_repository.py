"""User Repository Interface - Data access contract for users."""

from abc import ABC, abstractmethod

from ..entities import User
from ..value_objects import UserRole, UserStatus


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

    @abstractmethod
    async def get_by_iam_identity_id(self, iam_identity_id: str) -> User | None:
        """Get user by IAM identity ID (for SSO users)."""

    @abstractmethod
    async def list_users(
        self,
        offset: int = 0,
        limit: int = 20,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[User]:
        """List users with pagination and filters."""

    @abstractmethod
    async def count_users(
        self,
        role: UserRole | None = None,
        status: UserStatus | None = None,
    ) -> int:
        """Count users with optional filters."""
