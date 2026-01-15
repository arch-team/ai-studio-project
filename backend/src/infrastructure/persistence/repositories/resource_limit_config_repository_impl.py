"""ResourceLimitConfig Repository Implementation - SQLAlchemy data access."""

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.resource_limit_config import (
    LimitRole,
    PriorityDefault,
    ResourceLimitConfig,
)
from src.domain.repositories.resource_limit_config_repository import (
    IResourceLimitConfigRepository,
)
from src.infrastructure.persistence.models.resource_limit_config_model import (
    LimitRole as ModelLimitRole,
)
from src.infrastructure.persistence.models.resource_limit_config_model import (
    PriorityDefault as ModelPriorityDefault,
)
from src.infrastructure.persistence.models.resource_limit_config_model import (
    ResourceLimitConfigModel,
)


class ResourceLimitConfigRepository(IResourceLimitConfigRepository):
    """SQLAlchemy implementation of ResourceLimitConfig repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _model_to_entity(self, model: ResourceLimitConfigModel) -> ResourceLimitConfig:
        """Convert ORM model to domain entity."""
        return ResourceLimitConfig(
            id=model.id,
            config_name=model.config_name,
            role=LimitRole(model.role.value),
            project_id=model.project_id,
            max_gpu_per_job=model.max_gpu_per_job,
            max_cpu_per_job=model.max_cpu_per_job,
            max_memory_gb_per_job=model.max_memory_gb_per_job,
            max_storage_gb_per_job=model.max_storage_gb_per_job,
            max_nodes_per_job=model.max_nodes_per_job,
            priority_default=PriorityDefault(model.priority_default.value),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: ResourceLimitConfig) -> ResourceLimitConfigModel:
        """Convert domain entity to ORM model."""
        return ResourceLimitConfigModel(
            id=entity.id if entity.id else None,
            config_name=entity.config_name,
            role=ModelLimitRole(entity.role.value),
            project_id=entity.project_id,
            max_gpu_per_job=entity.max_gpu_per_job,
            max_cpu_per_job=entity.max_cpu_per_job,
            max_memory_gb_per_job=entity.max_memory_gb_per_job,
            max_storage_gb_per_job=entity.max_storage_gb_per_job,
            max_nodes_per_job=entity.max_nodes_per_job,
            priority_default=ModelPriorityDefault(entity.priority_default.value),
        )

    async def get_by_id(self, config_id: int) -> ResourceLimitConfig | None:
        """Get config by ID."""
        result = await self._session.execute(
            select(ResourceLimitConfigModel).where(
                ResourceLimitConfigModel.id == config_id
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_role_and_project(
        self, role: LimitRole, project_id: int | None
    ) -> ResourceLimitConfig | None:
        """Get config by role and project combination."""
        model_role = ModelLimitRole(role.value)

        if project_id is None:
            query = select(ResourceLimitConfigModel).where(
                and_(
                    ResourceLimitConfigModel.role == model_role,
                    ResourceLimitConfigModel.project_id.is_(None),
                )
            )
        else:
            query = select(ResourceLimitConfigModel).where(
                and_(
                    ResourceLimitConfigModel.role == model_role,
                    ResourceLimitConfigModel.project_id == project_id,
                )
            )

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

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
        query = select(ResourceLimitConfigModel)
        count_query = select(func.count(ResourceLimitConfigModel.id))

        # Apply role filter
        if role is not None:
            model_role = ModelLimitRole(role.value)
            query = query.where(ResourceLimitConfigModel.role == model_role)
            count_query = count_query.where(ResourceLimitConfigModel.role == model_role)

        # Apply project filter
        if project_id is not None:
            if include_global:
                # Include both project-specific and global configs
                project_condition = or_(
                    ResourceLimitConfigModel.project_id == project_id,
                    ResourceLimitConfigModel.project_id.is_(None),
                )
            else:
                # Only project-specific
                project_condition = ResourceLimitConfigModel.project_id == project_id
            query = query.where(project_condition)
            count_query = count_query.where(project_condition)

        # Get total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(
            ResourceLimitConfigModel, sort_by, ResourceLimitConfigModel.created_at
        )
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._model_to_entity(m) for m in models], total

    async def create(self, config: ResourceLimitConfig) -> ResourceLimitConfig:
        """Create a new config."""
        model = self._entity_to_model(config)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def update(self, config: ResourceLimitConfig) -> ResourceLimitConfig:
        """Update an existing config."""
        result = await self._session.execute(
            select(ResourceLimitConfigModel).where(
                ResourceLimitConfigModel.id == config.id
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"ResourceLimitConfig with id {config.id} not found")

        # Update fields
        model.config_name = config.config_name
        model.role = ModelLimitRole(config.role.value)
        model.project_id = config.project_id
        model.max_gpu_per_job = config.max_gpu_per_job
        model.max_cpu_per_job = config.max_cpu_per_job
        model.max_memory_gb_per_job = config.max_memory_gb_per_job
        model.max_storage_gb_per_job = config.max_storage_gb_per_job
        model.max_nodes_per_job = config.max_nodes_per_job
        model.priority_default = ModelPriorityDefault(config.priority_default.value)

        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def soft_delete(self, config_id: int) -> bool:
        """Soft delete a config (hard delete for now, no soft delete column)."""
        result = await self._session.execute(
            select(ResourceLimitConfigModel).where(
                ResourceLimitConfigModel.id == config_id
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def exists_by_role_and_project(
        self, role: LimitRole, project_id: int | None
    ) -> bool:
        """Check if config with role and project combination exists."""
        model_role = ModelLimitRole(role.value)

        if project_id is None:
            query = select(func.count(ResourceLimitConfigModel.id)).where(
                and_(
                    ResourceLimitConfigModel.role == model_role,
                    ResourceLimitConfigModel.project_id.is_(None),
                )
            )
        else:
            query = select(func.count(ResourceLimitConfigModel.id)).where(
                and_(
                    ResourceLimitConfigModel.role == model_role,
                    ResourceLimitConfigModel.project_id == project_id,
                )
            )

        result = await self._session.execute(query)
        count = result.scalar() or 0
        return count > 0


async def get_resource_limit_config_repository(
    session: AsyncSession,
) -> ResourceLimitConfigRepository:
    """Factory function for dependency injection."""
    return ResourceLimitConfigRepository(session)
