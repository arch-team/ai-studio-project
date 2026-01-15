"""Space Repository Interface - Data access contract for development spaces."""

from abc import ABC, abstractmethod

from ..entities import Space
from ..value_objects import SpaceStatus


class ISpaceRepository(ABC):
    """Abstract repository interface for Space entity."""

    @abstractmethod
    async def get_by_id(self, space_id: str) -> Space | None:
        """Get space by ID."""

    @abstractmethod
    async def get_by_name_and_owner(
        self, space_name: str, owner_id: int
    ) -> Space | None:
        """Get space by name and owner ID."""

    @abstractmethod
    async def list_spaces(
        self,
        owner_id: int | None = None,
        status: SpaceStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Space], int]:
        """List spaces with pagination and filters.

        Returns:
            tuple of (list of spaces, total count)
        """

    @abstractmethod
    async def create(self, space: Space) -> Space:
        """Create a new space."""

    @abstractmethod
    async def update(self, space: Space) -> Space:
        """Update an existing space."""

    @abstractmethod
    async def soft_delete(self, space_id: str) -> bool:
        """Soft delete a space.

        Returns:
            True if deleted, False if not found
        """
