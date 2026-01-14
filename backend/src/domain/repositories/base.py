"""Base Repository Interface - Generic repository contract.

Defines the standard CRUD operations that all repositories must implement.
Following the Repository pattern from Domain-Driven Design.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from uuid import UUID

# Type variable for entity types
T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Abstract base repository interface.

    All domain repositories should inherit from this interface
    and implement the required methods.
    """

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Retrieve an entity by its unique identifier.

        Args:
            id: The unique identifier of the entity.

        Returns:
            The entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Retrieve all entities with pagination.

        Args:
            limit: Maximum number of entities to return.
            offset: Number of entities to skip.

        Returns:
            List of entities.
        """
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add a new entity to the repository.

        Args:
            entity: The entity to add.

        Returns:
            The added entity with any generated fields populated.
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: The entity with updated values.

        Returns:
            The updated entity.
        """
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete an entity by its identifier.

        Args:
            id: The unique identifier of the entity to delete.

        Returns:
            True if the entity was deleted, False if not found.
        """
        pass

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """Check if an entity exists.

        Args:
            id: The unique identifier to check.

        Returns:
            True if the entity exists, False otherwise.
        """
        pass
