"""ResourceQuota Repository Implementation (T058-T060)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.quotas.domain.entities import ResourceQuota
from src.modules.quotas.domain.repositories import IResourceQuotaRepository
from src.modules.quotas.domain.value_objects import QuotaStatus, QuotaType
from src.modules.quotas.infrastructure.models import ResourceQuotaModel
from src.shared.utils import utc_now


class ResourceQuotaRepository(IResourceQuotaRepository):
    """SQLAlchemy implementation of ResourceQuota repository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self._session = session

    def _to_entity(self, model: ResourceQuotaModel) -> ResourceQuota:
        """Convert ORM model to domain entity."""
        return ResourceQuota(
            id=model.id,
            name=model.name,
            description=model.description,
            quota_type=model.quota_type,
            max_cpu_cores=model.max_cpu_cores,
            reserved_cpu_cores=model.reserved_cpu_cores,
            max_gpu_count=model.max_gpu_count,
            reserved_gpu_count=model.reserved_gpu_count,
            gpu_types=model.gpu_types or [],
            max_memory_gb=model.max_memory_gb,
            reserved_memory_gb=model.reserved_memory_gb,
            max_storage_gb=model.max_storage_gb,
            max_concurrent_jobs=model.max_concurrent_jobs,
            max_total_jobs=model.max_total_jobs,
            max_spot_instances=model.max_spot_instances,
            status=model.status,
            valid_from=model.valid_from,
            valid_until=model.valid_until,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: ResourceQuota) -> ResourceQuotaModel:
        """Convert domain entity to ORM model."""
        return ResourceQuotaModel(
            id=entity.id if entity.id else None,
            name=entity.name,
            description=entity.description,
            quota_type=entity.quota_type,
            max_cpu_cores=entity.max_cpu_cores,
            reserved_cpu_cores=entity.reserved_cpu_cores,
            max_gpu_count=entity.max_gpu_count,
            reserved_gpu_count=entity.reserved_gpu_count,
            gpu_types=entity.gpu_types if entity.gpu_types else None,
            max_memory_gb=entity.max_memory_gb,
            reserved_memory_gb=entity.reserved_memory_gb,
            max_storage_gb=entity.max_storage_gb,
            max_concurrent_jobs=entity.max_concurrent_jobs,
            max_total_jobs=entity.max_total_jobs,
            max_spot_instances=entity.max_spot_instances,
            status=entity.status,
            valid_from=entity.valid_from,
            valid_until=entity.valid_until,
            created_by=entity.created_by,
        )

    async def get_by_id(self, quota_id: int) -> ResourceQuota | None:
        """Get quota by ID."""
        stmt = select(ResourceQuotaModel).where(ResourceQuotaModel.id == quota_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_name(self, name: str) -> ResourceQuota | None:
        """Get quota by unique name."""
        stmt = select(ResourceQuotaModel).where(ResourceQuotaModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_quotas(
        self,
        quota_type: QuotaType | None = None,
        status: QuotaStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[ResourceQuota], int]:
        """List quotas with pagination and filters."""
        # Build base query
        stmt = select(ResourceQuotaModel)
        count_stmt = select(func.count(ResourceQuotaModel.id))

        # Apply filters
        if quota_type is not None:
            stmt = stmt.where(ResourceQuotaModel.quota_type == quota_type)
            count_stmt = count_stmt.where(ResourceQuotaModel.quota_type == quota_type)

        if status is not None:
            stmt = stmt.where(ResourceQuotaModel.status == status)
            count_stmt = count_stmt.where(ResourceQuotaModel.status == status)

        # Get total count
        result = await self._session.execute(count_stmt)
        total = result.scalar() or 0

        # Apply sorting
        sort_column = getattr(ResourceQuotaModel, sort_by, ResourceQuotaModel.created_at)
        if sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(sort_column.desc())

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        # Execute query
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models], total

    async def create(self, quota: ResourceQuota) -> ResourceQuota:
        """Create a new quota."""
        model = self._to_model(quota)
        model.id = None  # Ensure auto-increment
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, quota: ResourceQuota) -> ResourceQuota:
        """Update an existing quota."""
        stmt = select(ResourceQuotaModel).where(ResourceQuotaModel.id == quota.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"ResourceQuota with id {quota.id} not found")

        # Update fields
        model.name = quota.name
        model.description = quota.description
        model.quota_type = quota.quota_type
        model.max_cpu_cores = quota.max_cpu_cores
        model.reserved_cpu_cores = quota.reserved_cpu_cores
        model.max_gpu_count = quota.max_gpu_count
        model.reserved_gpu_count = quota.reserved_gpu_count
        model.gpu_types = quota.gpu_types if quota.gpu_types else None
        model.max_memory_gb = quota.max_memory_gb
        model.reserved_memory_gb = quota.reserved_memory_gb
        model.max_storage_gb = quota.max_storage_gb
        model.max_concurrent_jobs = quota.max_concurrent_jobs
        model.max_total_jobs = quota.max_total_jobs
        model.max_spot_instances = quota.max_spot_instances
        model.status = quota.status
        model.valid_from = quota.valid_from
        model.valid_until = quota.valid_until
        model.updated_at = utc_now()

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def soft_delete(self, quota_id: int) -> bool:
        """Soft delete a quota (set status to expired)."""
        stmt = select(ResourceQuotaModel).where(ResourceQuotaModel.id == quota_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        model.status = QuotaStatus.EXPIRED
        model.updated_at = utc_now()
        await self._session.flush()
        return True

    async def exists_by_name(self, name: str) -> bool:
        """Check if quota with name exists."""
        stmt = select(func.count(ResourceQuotaModel.id)).where(
            ResourceQuotaModel.name == name
        )
        result = await self._session.execute(stmt)
        count = result.scalar() or 0
        return count > 0
