"""ResourceQuota Repository Implementation."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository
from src.shared.utils import utc_now

from ...domain.entities import ResourceQuota
from ...domain.repositories import IResourceQuotaRepository
from ...domain.value_objects import QuotaStatus, QuotaType
from ..models import ResourceQuotaModel


class ResourceQuotaRepository(PydanticRepository[ResourceQuota, ResourceQuotaModel, int], IResourceQuotaRepository):
    """SQLAlchemy implementation of ResourceQuota repository."""

    _entity_class = ResourceQuota
    _updatable_fields = [
        "name",
        "description",
        "quota_type",
        "max_cpu_cores",
        "reserved_cpu_cores",
        "max_gpu_count",
        "reserved_gpu_count",
        "gpu_types",
        "max_memory_gb",
        "reserved_memory_gb",
        "max_storage_gb",
        "max_concurrent_jobs",
        "max_total_jobs",
        "max_spot_instances",
        "status",
        "valid_from",
        "valid_until",
    ]

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ResourceQuotaModel)

    # ========== IResourceQuotaRepository 接口方法 ==========

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
        stmt = select(func.count(ResourceQuotaModel.id)).where(ResourceQuotaModel.name == name)
        result = await self._session.execute(stmt)
        count = result.scalar() or 0
        return count > 0
