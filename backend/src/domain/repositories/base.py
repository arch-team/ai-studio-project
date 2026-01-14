"""Base Repository Interface - Generic repository contract for DDD."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

# Type variable for entity types
T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Abstract base repository interface."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> T | None:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add entity to repository."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists."""
        pass
