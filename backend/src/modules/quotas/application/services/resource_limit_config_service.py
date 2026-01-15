"""ResourceLimitConfig Service - Business logic for resource limit management."""

from src.modules.quotas.domain.entities import ResourceLimitConfig
from src.modules.quotas.domain.exceptions import DuplicateConfigError, QuotaNotFoundError
from src.modules.quotas.domain.repositories import IResourceLimitConfigRepository
from src.modules.quotas.domain.value_objects import LimitRole, PriorityDefault


class ResourceLimitConfigService:
    """Service for managing resource limit configurations."""

    def __init__(self, repository: IResourceLimitConfigRepository):
        self._repository = repository

    async def create_config(self, data: dict) -> ResourceLimitConfig:
        """Create a new resource limit config.

        Raises:
            DuplicateConfigError: If config with same role+project exists
        """
        role = LimitRole(data["role"])
        project_id = data.get("project_id")

        # Check for duplicate (role, project_id) combination
        if await self._repository.exists_by_role_and_project(role, project_id):
            scope = f"project {project_id}" if project_id else "global"
            raise DuplicateConfigError(role.value, scope)

        # Map priority_default
        priority_default = PriorityDefault.MEDIUM
        if data.get("priority_default"):
            priority_default = PriorityDefault(data["priority_default"])

        # Create domain entity
        config = ResourceLimitConfig(
            id=0,  # Will be set by database
            config_name=data["config_name"],
            role=role,
            project_id=project_id,
            max_gpu_per_job=data.get("max_gpu_per_job", 8),
            max_cpu_per_job=data.get("max_cpu_per_job", 64),
            max_memory_gb_per_job=data.get("max_memory_gb_per_job", 512),
            max_storage_gb_per_job=data.get("max_storage_gb_per_job", 1000),
            max_nodes_per_job=data.get("max_nodes_per_job", 4),
            priority_default=priority_default,
        )

        return await self._repository.create(config)

    async def get_config(self, config_id: int) -> ResourceLimitConfig:
        """Get config by ID."""
        config = await self._repository.get_by_id(config_id)
        if config is None:
            raise QuotaNotFoundError(str(config_id))
        return config

    async def get_config_for_role(
        self, role: LimitRole, project_id: int | None = None
    ) -> ResourceLimitConfig | None:
        """Get config for a specific role and project.

        First tries to find project-specific config, then falls back to global.
        """
        if project_id is not None:
            # Try project-specific first
            config = await self._repository.get_by_role_and_project(role, project_id)
            if config is not None:
                return config

        # Fall back to global config
        return await self._repository.get_by_role_and_project(role, None)

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
        """List configs with filters and pagination."""
        return await self._repository.list_configs(
            role=role,
            project_id=project_id,
            include_global=include_global,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def update_config(
        self, config_id: int, data: dict
    ) -> ResourceLimitConfig:
        """Update an existing config.

        Raises:
            QuotaNotFoundError: If config not found
            DuplicateConfigError: If new role+project combination already exists
        """
        config = await self._repository.get_by_id(config_id)
        if config is None:
            raise QuotaNotFoundError(str(config_id))

        # Check if changing role or project_id would create duplicate
        new_role = LimitRole(data["role"]) if "role" in data else config.role
        new_project_id = data.get("project_id", config.project_id)

        if new_role != config.role or new_project_id != config.project_id:
            existing = await self._repository.get_by_role_and_project(
                new_role, new_project_id
            )
            if existing is not None and existing.id != config_id:
                scope = f"project {new_project_id}" if new_project_id else "global"
                raise DuplicateConfigError(new_role.value, scope)

        # Update fields
        if "config_name" in data:
            config.config_name = data["config_name"]
        if "role" in data:
            config.role = LimitRole(data["role"])
        if "project_id" in data:
            config.project_id = data["project_id"]
        if "max_gpu_per_job" in data:
            config.max_gpu_per_job = data["max_gpu_per_job"]
        if "max_cpu_per_job" in data:
            config.max_cpu_per_job = data["max_cpu_per_job"]
        if "max_memory_gb_per_job" in data:
            config.max_memory_gb_per_job = data["max_memory_gb_per_job"]
        if "max_storage_gb_per_job" in data:
            config.max_storage_gb_per_job = data["max_storage_gb_per_job"]
        if "max_nodes_per_job" in data:
            config.max_nodes_per_job = data["max_nodes_per_job"]
        if "priority_default" in data:
            config.priority_default = PriorityDefault(data["priority_default"])

        return await self._repository.update(config)

    async def delete_config(self, config_id: int) -> None:
        """Delete a config.

        Raises:
            QuotaNotFoundError: If config not found
        """
        config = await self._repository.get_by_id(config_id)
        if config is None:
            raise QuotaNotFoundError(str(config_id))

        await self._repository.soft_delete(config_id)

    async def validate_job_limits(
        self,
        role: LimitRole,
        project_id: int | None,
        requested_gpu: int,
        requested_cpu: int,
        requested_memory_gb: int,
        requested_storage_gb: int,
        requested_nodes: int,
    ) -> tuple[bool, str | None]:
        """Validate if requested resources are within limits for a role.

        Returns:
            Tuple of (is_valid, error_message)
        """
        config = await self.get_config_for_role(role, project_id)
        if config is None:
            # No limits configured, allow by default
            return True, None

        errors = []
        if requested_gpu > config.max_gpu_per_job:
            errors.append(
                f"GPU ({requested_gpu}) exceeds limit ({config.max_gpu_per_job})"
            )
        if requested_cpu > config.max_cpu_per_job:
            errors.append(
                f"CPU ({requested_cpu}) exceeds limit ({config.max_cpu_per_job})"
            )
        if requested_memory_gb > config.max_memory_gb_per_job:
            errors.append(
                f"Memory ({requested_memory_gb}GB) exceeds limit "
                f"({config.max_memory_gb_per_job}GB)"
            )
        if requested_storage_gb > config.max_storage_gb_per_job:
            errors.append(
                f"Storage ({requested_storage_gb}GB) exceeds limit "
                f"({config.max_storage_gb_per_job}GB)"
            )
        if requested_nodes > config.max_nodes_per_job:
            errors.append(
                f"Nodes ({requested_nodes}) exceeds limit ({config.max_nodes_per_job})"
            )

        if errors:
            return False, "; ".join(errors)
        return True, None
