"""Model Repository Implementation - SQLAlchemy data access."""

from sqlalchemy import func, select
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
        query = select(ModelModel).options(selectinload(ModelModel.owner))
        count_query = select(func.count(ModelModel.id))

        # Apply filters
        if owner_id is not None:
            query = query.where(ModelModel.owner_id == owner_id)
            count_query = count_query.where(ModelModel.owner_id == owner_id)

        if training_job_id is not None:
            query = query.where(ModelModel.training_job_id == training_job_id)
            count_query = count_query.where(ModelModel.training_job_id == training_job_id)

        if status is not None:
            if isinstance(status, str):
                status_enum = ModelStatus[status.upper()]
            else:
                status_enum = status
            query = query.where(ModelModel.status == status_enum)
            count_query = count_query.where(ModelModel.status == status_enum)

        if framework is not None:
            if isinstance(framework, str):
                framework_enum = ModelFramework[framework.upper()]
            else:
                framework_enum = framework
            query = query.where(ModelModel.framework == framework_enum)
            count_query = count_query.where(ModelModel.framework == framework_enum)

        # Get total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(ModelModel, sort_by, ModelModel.created_at)
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
