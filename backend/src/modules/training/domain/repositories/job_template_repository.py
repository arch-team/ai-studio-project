"""Job Template Repository Interface - Data access contract for job templates."""

from abc import ABC, abstractmethod

from ..entities import JobTemplate
from ..value_objects import TemplateVisibility


class IJobTemplateRepository(ABC):
    """Abstract repository interface for JobTemplate entity."""

    @abstractmethod
    async def get_by_id(self, template_id: int) -> JobTemplate | None:
        """Get job template by ID (excludes soft deleted)."""

    @abstractmethod
    async def list_templates(
        self,
        owner_id: int | None = None,
        visibility: TemplateVisibility | None = None,
        search_name: str | None = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "usage_count",
        sort_order: str = "desc",
    ) -> tuple[list[JobTemplate], int]:
        """List templates with pagination and filters.

        Returns:
            tuple of (list of templates, total count)
        """

    @abstractmethod
    async def list_visible_templates(
        self,
        user_id: int,
        search_name: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "usage_count",
        sort_order: str = "desc",
    ) -> tuple[list[JobTemplate], int]:
        """List templates visible to a user (own + public).

        Returns:
            tuple of (list of templates, total count)
        """

    @abstractmethod
    async def get_popular_templates(self, limit: int = 10) -> list[JobTemplate]:
        """Get most used public templates."""

    @abstractmethod
    async def create(self, template: JobTemplate) -> JobTemplate:
        """Create a new job template."""

    @abstractmethod
    async def update(self, template: JobTemplate) -> JobTemplate:
        """Update an existing job template."""

    @abstractmethod
    async def soft_delete(self, template_id: int) -> bool:
        """Soft delete a job template.

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    async def increment_usage_count(self, template_id: int) -> None:
        """Atomically increment usage count and update last_used_at."""

    @abstractmethod
    async def exists_by_name_and_owner(self, name: str, owner_id: int) -> bool:
        """Check if a template with the given name exists for the owner."""
