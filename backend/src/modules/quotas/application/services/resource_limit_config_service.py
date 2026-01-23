"""ResourceLimitConfig Service - Business logic for resource limit management."""

from src.modules.quotas.domain.entities import ResourceLimitConfig
from src.modules.quotas.domain.exceptions import DuplicateConfigError, QuotaNotFoundError
from src.modules.quotas.domain.repositories import IResourceLimitConfigRepository
from src.modules.quotas.domain.value_objects import LimitRole, PriorityDefault
from src.shared.application import BaseService


class ResourceLimitConfigService(BaseService[ResourceLimitConfig, int]):
    """Service for managing resource limit configurations."""

    _not_found_error_factory = QuotaNotFoundError

    # 资源限制字段映射
    _RESOURCE_LIMITS = {
        "max_gpu_per_job": ("GPU", 8),
        "max_cpu_per_job": ("CPU", 64),
        "max_memory_gb_per_job": ("Memory", 512),
        "max_storage_gb_per_job": ("Storage", 1000),
        "max_nodes_per_job": ("Nodes", 4),
    }

    # 可更新字段列表
    _UPDATABLE_FIELDS = [
        "config_name",
        "role",
        "project_id",
        "max_gpu_per_job",
        "max_cpu_per_job",
        "max_memory_gb_per_job",
        "max_storage_gb_per_job",
        "max_nodes_per_job",
        "priority_default",
    ]

    def __init__(self, repository: IResourceLimitConfigRepository):
        super().__init__(repository, "ResourceLimitConfig")

    async def _check_duplicate_config(
        self, role: LimitRole, project_id: int | None, exclude_id: int | None = None
    ) -> None:
        """检查配置是否重复."""
        existing = await self._repository.get_by_role_and_project(role, project_id)
        if existing and (exclude_id is None or existing.id != exclude_id):
            scope = f"project {project_id}" if project_id else "global"
            raise DuplicateConfigError(role.value, scope)

    def _build_config_entity(self, data: dict, config_id: int = 0) -> ResourceLimitConfig:
        """构建配置实体."""
        return ResourceLimitConfig(
            id=config_id,
            config_name=data["config_name"],
            role=LimitRole(data["role"]),
            project_id=data.get("project_id"),
            max_gpu_per_job=data.get("max_gpu_per_job", self._RESOURCE_LIMITS["max_gpu_per_job"][1]),
            max_cpu_per_job=data.get("max_cpu_per_job", self._RESOURCE_LIMITS["max_cpu_per_job"][1]),
            max_memory_gb_per_job=data.get("max_memory_gb_per_job", self._RESOURCE_LIMITS["max_memory_gb_per_job"][1]),
            max_storage_gb_per_job=data.get("max_storage_gb_per_job", self._RESOURCE_LIMITS["max_storage_gb_per_job"][1]),
            max_nodes_per_job=data.get("max_nodes_per_job", self._RESOURCE_LIMITS["max_nodes_per_job"][1]),
            priority_default=PriorityDefault(data.get("priority_default", PriorityDefault.MEDIUM.value)),
        )

    async def create_config(self, data: dict) -> ResourceLimitConfig:
        """Create a new resource limit config."""
        role = LimitRole(data["role"])
        project_id = data.get("project_id")

        # 检查重复配置
        await self._check_duplicate_config(role, project_id)

        # 构建并保存配置
        config = self._build_config_entity(data)
        return await self._repository.create(config)

    async def get_config(self, config_id: int) -> ResourceLimitConfig:
        """Get config by ID."""
        return await self._get_or_raise(config_id)

    async def get_config_for_role(
        self, role: LimitRole, project_id: int | None = None
    ) -> ResourceLimitConfig | None:
        """Get config for a specific role and project.

        First tries to find project-specific config, then falls back to global.
        """
        # 优先查找项目特定配置
        if project_id is not None:
            config = await self._repository.get_by_role_and_project(role, project_id)
            if config is not None:
                return config

        # 回退到全局配置
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

    def _update_config_fields(self, config: ResourceLimitConfig, data: dict) -> None:
        """更新配置字段."""
        for field in self._UPDATABLE_FIELDS:
            if field not in data:
                continue

            value = data[field]
            if field == "role":
                value = LimitRole(value)
            elif field == "priority_default":
                value = PriorityDefault(value)

            setattr(config, field, value)

    async def update_config(
        self, config_id: int, data: dict
    ) -> ResourceLimitConfig:
        """Update an existing config."""
        config = await self._get_or_raise(config_id)

        # 检查角色和项目组合是否会导致重复
        new_role = LimitRole(data["role"]) if "role" in data else config.role
        new_project_id = data.get("project_id", config.project_id)

        if new_role != config.role or new_project_id != config.project_id:
            await self._check_duplicate_config(new_role, new_project_id, config_id)

        # 更新字段
        self._update_config_fields(config, data)

        return await self._repository.update(config)

    async def delete_config(self, config_id: int) -> None:
        """Delete a config."""
        await self._get_or_raise(config_id)
        await self._repository.soft_delete(config_id)

    def _check_resource_limit(
        self, requested: int, limit: int, resource_name: str, errors: list[str]
    ) -> None:
        """检查单个资源限制."""
        if requested > limit:
            unit = "GB" if "memory" in resource_name.lower() or "storage" in resource_name.lower() else ""
            errors.append(
                f"{resource_name} ({requested}{unit}) exceeds limit ({limit}{unit})"
            )

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
            # 无限制配置，默认允许
            return True, None

        # 验证各项资源限制
        errors = []
        validations = [
            (requested_gpu, config.max_gpu_per_job, "GPU"),
            (requested_cpu, config.max_cpu_per_job, "CPU"),
            (requested_memory_gb, config.max_memory_gb_per_job, "Memory"),
            (requested_storage_gb, config.max_storage_gb_per_job, "Storage"),
            (requested_nodes, config.max_nodes_per_job, "Nodes"),
        ]

        for requested, limit, resource_name in validations:
            self._check_resource_limit(requested, limit, resource_name, errors)

        if errors:
            return False, "; ".join(errors)
        return True, None