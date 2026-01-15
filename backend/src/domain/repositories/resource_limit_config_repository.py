"""ResourceLimitConfig Repository Interface - Abstract data access contract."""

from abc import ABC, abstractmethod

from src.domain.entities.resource_limit_config import LimitRole, ResourceLimitConfig


class IResourceLimitConfigRepository(ABC):
    """Abstract repository interface for ResourceLimitConfig."""

    @abstractmethod
    async def get_by_id(self, config_id: int) -> ResourceLimitConfig | None:
        """Get config by ID."""

    @abstractmethod
    async def get_by_role_and_project(
        self, role: LimitRole, project_id: int | None
    ) -> ResourceLimitConfig | None:
        """Get config by role and project combination."""

    @abstractmethod
    async def list_configs(
        self,
        role: LimitRole | None = None,
        project_id: int | None = None,
        include_global: bool = True,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[ResourceLimitConfig], int]:
        """List configs with pagination and filters."""

    @abstractmethod
    async def create(self, config: ResourceLimitConfig) -> ResourceLimitConfig:
        """Create a new config."""

    @abstractmethod
    async def update(self, config: ResourceLimitConfig) -> ResourceLimitConfig:
        """Update an existing config."""

    @abstractmethod
    async def soft_delete(self, config_id: int) -> bool:
        """Soft delete a config."""

    @abstractmethod
    async def exists_by_role_and_project(
        self, role: LimitRole, project_id: int | None
    ) -> bool:
        """Check if config with role and project combination exists."""
