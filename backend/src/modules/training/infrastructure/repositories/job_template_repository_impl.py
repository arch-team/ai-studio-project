"""JobTemplate Repository Implementation - SQLAlchemy data access."""

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository
from src.shared.utils import utc_now

from ...domain.entities import JobTemplate
from ...domain.repositories import IJobTemplateRepository
from ...domain.value_objects import TemplateVisibility
from ..models import JobTemplateModel


class JobTemplateRepository(
    PydanticRepository[JobTemplate, JobTemplateModel, int],
    IJobTemplateRepository,
):
    """SQLAlchemy implementation of JobTemplate repository."""

    _entity_class = JobTemplate
    _updatable_fields = [
        "name",
        "description",
        "visibility",
        "training_config",
        "usage_count",
        "last_used_at",
        "deleted_at",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, JobTemplateModel)

    # ========== Override get_by_id to exclude soft deleted ==========

    async def get_by_id(self, template_id: int) -> JobTemplate | None:
        """Get job template by ID (excludes soft deleted)."""
        result = await self._session.execute(
            select(JobTemplateModel).where(
                and_(
                    JobTemplateModel.id == template_id,
                    JobTemplateModel.deleted_at.is_(None),
                )
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    # ========== IJobTemplateRepository 接口方法 ==========

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
        """List templates with pagination and filters."""
        query = select(JobTemplateModel)
        count_query = select(func.count(JobTemplateModel.id))

        # Exclude soft deleted unless explicitly requested
        if not include_deleted:
            query = query.where(JobTemplateModel.deleted_at.is_(None))
            count_query = count_query.where(JobTemplateModel.deleted_at.is_(None))

        # Apply filters
        if owner_id is not None:
            query = query.where(JobTemplateModel.owner_id == owner_id)
            count_query = count_query.where(JobTemplateModel.owner_id == owner_id)

        if visibility is not None:
            query = query.where(JobTemplateModel.visibility == visibility)
            count_query = count_query.where(JobTemplateModel.visibility == visibility)

        if search_name is not None:
            search_pattern = f"%{search_name}%"
            query = query.where(JobTemplateModel.name.ilike(search_pattern))
            count_query = count_query.where(JobTemplateModel.name.ilike(search_pattern))

        # Get total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(JobTemplateModel, sort_by, JobTemplateModel.usage_count)
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

    async def list_visible_templates(
        self,
        user_id: int,
        search_name: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "usage_count",
        sort_order: str = "desc",
    ) -> tuple[list[JobTemplate], int]:
        """List templates visible to a user (own + public)."""
        visibility_condition = or_(
            JobTemplateModel.owner_id == user_id,
            JobTemplateModel.visibility == TemplateVisibility.PUBLIC,
        )

        query = select(JobTemplateModel).where(
            and_(
                JobTemplateModel.deleted_at.is_(None),
                visibility_condition,
            )
        )
        count_query = select(func.count(JobTemplateModel.id)).where(
            and_(
                JobTemplateModel.deleted_at.is_(None),
                visibility_condition,
            )
        )

        # Apply search filter
        if search_name is not None:
            search_pattern = f"%{search_name}%"
            query = query.where(JobTemplateModel.name.ilike(search_pattern))
            count_query = count_query.where(JobTemplateModel.name.ilike(search_pattern))

        # Get total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(JobTemplateModel, sort_by, JobTemplateModel.usage_count)
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

    async def get_popular_templates(self, limit: int = 10) -> list[JobTemplate]:
        """Get most used public templates."""
        query = (
            select(JobTemplateModel)
            .where(
                and_(
                    JobTemplateModel.deleted_at.is_(None),
                    JobTemplateModel.visibility == TemplateVisibility.PUBLIC,
                )
            )
            .order_by(JobTemplateModel.usage_count.desc())
            .limit(limit)
        )

        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models]

    async def soft_delete(self, template_id: int) -> bool:
        """Soft delete a job template."""
        result = await self._session.execute(
            select(JobTemplateModel).where(
                and_(
                    JobTemplateModel.id == template_id,
                    JobTemplateModel.deleted_at.is_(None),
                )
            )
        )
        model = result.scalar_one_or_none()

        if model is None:
            return False

        model.deleted_at = utc_now()
        await self._session.flush()
        return True

    async def increment_usage_count(self, template_id: int) -> None:
        """Atomically increment usage count and update last_used_at."""
        stmt = (
            update(JobTemplateModel)
            .where(JobTemplateModel.id == template_id)
            .values(
                usage_count=JobTemplateModel.usage_count + 1,
                last_used_at=utc_now(),
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def exists_by_name_and_owner(self, name: str, owner_id: int) -> bool:
        """Check if a template with the given name exists for the owner."""
        result = await self._session.execute(
            select(func.count(JobTemplateModel.id)).where(
                and_(
                    JobTemplateModel.name == name,
                    JobTemplateModel.owner_id == owner_id,
                    JobTemplateModel.deleted_at.is_(None),
                )
            )
        )
        count = result.scalar() or 0
        return count > 0
