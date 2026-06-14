"""JobTemplate Repository Implementation - SQLAlchemy data access."""

from typing import Any

from sqlalchemy import Select, and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository
from src.shared.utils import calculate_offset, utc_now

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
        # 构建基础查询
        query = select(JobTemplateModel)
        count_query = select(func.count(JobTemplateModel.id))

        # 应用过滤条件
        query, count_query = self._apply_template_filters(
            query, count_query, owner_id, visibility, search_name, include_deleted
        )

        # 执行分页查询
        return await self._execute_paginated_query(query, count_query, page, page_size, sort_by, sort_order)

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
        # 构建可见性条件
        visibility_condition = or_(
            JobTemplateModel.owner_id == user_id,
            JobTemplateModel.visibility == TemplateVisibility.PUBLIC,
        )

        # 构建查询
        query = select(JobTemplateModel).where(and_(JobTemplateModel.deleted_at.is_(None), visibility_condition))
        count_query = select(func.count(JobTemplateModel.id)).where(
            and_(JobTemplateModel.deleted_at.is_(None), visibility_condition)
        )

        # 应用搜索过滤
        if search_name:
            query, count_query = self._apply_search_filter(query, count_query, search_name)

        # 执行分页查询
        return await self._execute_paginated_query(query, count_query, page, page_size, sort_by, sort_order)

    def _apply_template_filters(
        self,
        query: Select[Any],
        count_query: Select[Any],
        owner_id: int | None,
        visibility: TemplateVisibility | None,
        search_name: str | None,
        include_deleted: bool,
    ) -> tuple[Select[Any], Select[Any]]:
        """应用模板过滤条件."""
        # 排除软删除
        if not include_deleted:
            query = query.where(JobTemplateModel.deleted_at.is_(None))
            count_query = count_query.where(JobTemplateModel.deleted_at.is_(None))

        # 所有者过滤
        if owner_id is not None:
            query = query.where(JobTemplateModel.owner_id == owner_id)
            count_query = count_query.where(JobTemplateModel.owner_id == owner_id)

        # 可见性过滤
        if visibility is not None:
            query = query.where(JobTemplateModel.visibility == visibility)
            count_query = count_query.where(JobTemplateModel.visibility == visibility)

        # 名称搜索
        if search_name:
            query, count_query = self._apply_search_filter(query, count_query, search_name)

        return query, count_query

    def _apply_search_filter(
        self, query: Select[Any], count_query: Select[Any], search_name: str
    ) -> tuple[Select[Any], Select[Any]]:
        """应用名称搜索过滤."""
        search_pattern = f"%{search_name}%"
        query = query.where(JobTemplateModel.name.ilike(search_pattern))
        count_query = count_query.where(JobTemplateModel.name.ilike(search_pattern))
        return query, count_query

    async def _execute_paginated_query(
        self,
        query: Select[Any],
        count_query: Select[Any],
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[JobTemplate], int]:
        """执行分页查询."""
        # 获取总数
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # 应用排序
        sort_column = getattr(JobTemplateModel, sort_by, JobTemplateModel.usage_count)
        query = query.order_by(sort_column.desc() if sort_order.lower() == "desc" else sort_column.asc())

        # 应用分页
        offset = calculate_offset(page, page_size)
        query = query.offset(offset).limit(page_size)

        # 执行查询
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
