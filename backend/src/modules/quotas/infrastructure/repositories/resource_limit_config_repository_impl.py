"""ResourceLimitConfig Repository Implementation - SQLAlchemy data access."""

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository

from ...domain.entities import ResourceLimitConfig
from ...domain.repositories import IResourceLimitConfigRepository
from ...domain.value_objects import LimitRole
from ..models import ResourceLimitConfigModel


class ResourceLimitConfigRepository(
    PydanticRepository[ResourceLimitConfig, ResourceLimitConfigModel, int], IResourceLimitConfigRepository
):
    """SQLAlchemy implementation of ResourceLimitConfig repository."""

    _entity_class = ResourceLimitConfig
    _updatable_fields = [
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

    def __init__(self, session: AsyncSession):
        super().__init__(session, ResourceLimitConfigModel)

    # ========== IResourceLimitConfigRepository 接口方法 ==========

    async def get_by_role_and_project(self, role: LimitRole, project_id: int | None) -> ResourceLimitConfig | None:
        """Get config by role and project combination."""
        if project_id is None:
            query = select(ResourceLimitConfigModel).where(
                and_(
                    ResourceLimitConfigModel.role == role,
                    ResourceLimitConfigModel.project_id.is_(None),
                )
            )
        else:
            query = select(ResourceLimitConfigModel).where(
                and_(
                    ResourceLimitConfigModel.role == role,
                    ResourceLimitConfigModel.project_id == project_id,
                )
            )

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

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
            query = query.where(ResourceLimitConfigModel.role == role)
            count_query = count_query.where(ResourceLimitConfigModel.role == role)

        # Apply project filter
        if project_id is not None:
            if include_global:
                project_condition = or_(
                    ResourceLimitConfigModel.project_id == project_id,
                    ResourceLimitConfigModel.project_id.is_(None),
                )
            else:
                project_condition = ResourceLimitConfigModel.project_id == project_id
            query = query.where(project_condition)
            count_query = count_query.where(project_condition)

        # Get total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(ResourceLimitConfigModel, sort_by, ResourceLimitConfigModel.created_at)
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

        return [self._to_entity(m) for m in models], total

    async def create(self, config: ResourceLimitConfig) -> ResourceLimitConfig:
        """Create a new config."""
        return await self.add(config)

    async def soft_delete(self, config_id: int) -> bool:
        """Soft delete a config (hard delete for now, no soft delete column)."""
        result = await self._session.execute(
            select(ResourceLimitConfigModel).where(ResourceLimitConfigModel.id == config_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def exists_by_role_and_project(self, role: LimitRole, project_id: int | None) -> bool:
        """Check if config with role and project combination exists."""
        if project_id is None:
            query = select(func.count(ResourceLimitConfigModel.id)).where(
                and_(
                    ResourceLimitConfigModel.role == role,
                    ResourceLimitConfigModel.project_id.is_(None),
                )
            )
        else:
            query = select(func.count(ResourceLimitConfigModel.id)).where(
                and_(
                    ResourceLimitConfigModel.role == role,
                    ResourceLimitConfigModel.project_id == project_id,
                )
            )

        result = await self._session.execute(query)
        count = result.scalar() or 0
        return count > 0
