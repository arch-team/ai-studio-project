"""Model Repository Implementation - SQLAlchemy data access."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.infrastructure import PydanticRepository
from src.shared.utils import utc_now

from ...domain.entities import Model
from ...domain.repositories import IModelRepository
from ...domain.value_objects import ModelFramework, ModelStatus
from ..models import ModelModel


class ModelRepository(PydanticRepository[Model, ModelModel, int], IModelRepository):
    """SQLAlchemy implementation of model repository."""

    _entity_class = Model
    _updatable_fields = [
        "model_name",
        "owner_id",
        "version",
        "display_name",
        "description",
        "training_job_id",
        "checkpoint_id",
        "model_uri",
        "registry_arn",
        "registry_status",
        "metrics",
        "hyperparameters",
        "framework",
        "framework_version",
        "status",
        "size_bytes",
        "model_format",
        "tags",
        "registered_at",
        "archived_at",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, ModelModel)

    # ========== IModelRepository 接口方法 ==========

    async def get_by_id(self, model_id: int) -> Model | None:
        """Get model by ID with owner preloaded."""
        result = await self._session.execute(
            select(ModelModel).options(selectinload(ModelModel.owner)).where(ModelModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_name_and_version(self, model_name: str, version: str) -> Model | None:
        """Get model by name and version."""
        result = await self._session.execute(
            select(ModelModel)
            .options(selectinload(ModelModel.owner))
            .where(ModelModel.model_name == model_name, ModelModel.version == version)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_latest_version(self, model_name: str) -> Model | None:
        """Get the latest version of a model by name."""
        result = await self._session.execute(
            select(ModelModel)
            .options(selectinload(ModelModel.owner))
            .where(ModelModel.model_name == model_name)
            .order_by(ModelModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_models(
        self,
        owner_id: int | None = None,
        training_job_id: int | None = None,
        status: str | ModelStatus | None = None,
        framework: str | ModelFramework | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Model], int]:
        """List models with pagination and filters."""
        # 构建查询
        query = select(ModelModel).options(selectinload(ModelModel.owner))
        count_query = select(func.count(ModelModel.id))

        # 应用过滤条件
        query, count_query = self._apply_model_filters(query, count_query, owner_id, training_job_id, status, framework)

        # 获取总数
        total = await self._get_total_count(count_query)

        # 应用排序和分页
        query = self._apply_sorting(query, sort_by, sort_order)
        query = self._apply_pagination(query, page, page_size)

        # 执行查询
        models = await self._execute_model_query(query)
        return [self._to_entity(m) for m in models], total

    def _apply_model_filters(
        self,
        query: Select[Any],
        count_query: Select[Any],
        owner_id: int | None,
        training_job_id: int | None,
        status: str | ModelStatus | None,
        framework: str | ModelFramework | None,
    ) -> tuple[Select[Any], Select[Any]]:
        """应用过滤条件到查询."""
        if owner_id is not None:
            query = query.where(ModelModel.owner_id == owner_id)
            count_query = count_query.where(ModelModel.owner_id == owner_id)

        if training_job_id is not None:
            query = query.where(ModelModel.training_job_id == training_job_id)
            count_query = count_query.where(ModelModel.training_job_id == training_job_id)

        if status is not None:
            status_enum = ModelStatus[status.upper()] if isinstance(status, str) else status
            query = query.where(ModelModel.status == status_enum)
            count_query = count_query.where(ModelModel.status == status_enum)

        if framework is not None:
            framework_enum = ModelFramework[framework.upper()] if isinstance(framework, str) else framework
            query = query.where(ModelModel.framework == framework_enum)
            count_query = count_query.where(ModelModel.framework == framework_enum)

        return query, count_query

    async def _get_total_count(self, count_query: Select[Any]) -> int:
        """获取总记录数."""
        result = await self._session.execute(count_query)
        return result.scalar() or 0

    def _apply_sorting(self, query: Select[Any], sort_by: str, sort_order: str) -> Select[Any]:
        """应用排序."""
        sort_column = getattr(ModelModel, sort_by, ModelModel.created_at)
        return query.order_by(sort_column.desc() if sort_order.lower() == "desc" else sort_column.asc())

    def _apply_pagination(self, query: Select[Any], page: int, page_size: int) -> Select[Any]:
        """应用分页."""
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)

    async def _execute_model_query(self, query: Select[Any]) -> Sequence[Any]:
        """执行查询并返回模型列表."""
        result = await self._session.execute(query)
        return result.scalars().all()

    async def list_versions(self, model_name: str) -> list[Model]:
        """List all versions of a model by name."""
        result = await self._session.execute(
            select(ModelModel)
            .options(selectinload(ModelModel.owner))
            .where(ModelModel.model_name == model_name)
            .order_by(ModelModel.created_at.asc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def soft_delete(self, model_id: int) -> bool:
        """Soft delete a model (archive it)."""
        result = await self._session.execute(select(ModelModel).where(ModelModel.id == model_id))
        model = result.scalar_one_or_none()
        if model is None:
            return False

        model.status = ModelStatus.ARCHIVED
        model.archived_at = utc_now()
        model.updated_at = utc_now()
        await self._session.flush()
        return True
