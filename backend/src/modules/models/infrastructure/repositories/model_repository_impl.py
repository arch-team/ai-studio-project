"""Model Repository Implementation - SQLAlchemy data access."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.models.domain.entities import Model
from src.modules.models.domain.repositories import IModelRepository
from src.modules.models.domain.value_objects import ModelFramework, ModelStatus
from src.modules.models.infrastructure.models import ModelModel
from src.shared.infrastructure.repository_base import EnhancedBaseRepository
from src.shared.utils import utc_now


class ModelRepository(EnhancedBaseRepository[Model, ModelModel, int], IModelRepository):
    """SQLAlchemy implementation of model repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ModelModel)

    def _to_entity(self, model: ModelModel) -> Model:
        """Convert ORM model to domain entity."""
        return Model(
            id=model.id,
            model_name=model.model_name,
            owner_id=model.owner_id,
            version=model.version,
            display_name=model.display_name,
            description=model.description,
            training_job_id=model.training_job_id,
            checkpoint_id=model.checkpoint_id,
            model_uri=model.model_uri,
            registry_arn=model.registry_arn,
            registry_status=model.registry_status,
            metrics=model.metrics,
            hyperparameters=model.hyperparameters,
            framework=model.framework,
            framework_version=model.framework_version,
            status=model.status,
            size_bytes=model.size_bytes,
            model_format=model.model_format,
            tags=model.tags,
            created_at=model.created_at,
            updated_at=model.updated_at,
            registered_at=model.registered_at,
            archived_at=model.archived_at,
        )

    def _to_model(self, entity: Model) -> ModelModel:
        """Convert domain entity to ORM model."""
        return ModelModel(
            id=entity.id if entity.id else None,
            model_name=entity.model_name,
            owner_id=entity.owner_id,
            version=entity.version,
            display_name=entity.display_name,
            description=entity.description,
            training_job_id=entity.training_job_id,
            checkpoint_id=entity.checkpoint_id,
            model_uri=entity.model_uri,
            registry_arn=entity.registry_arn,
            registry_status=entity.registry_status,
            metrics=entity.metrics,
            hyperparameters=entity.hyperparameters,
            framework=entity.framework,
            framework_version=entity.framework_version,
            status=entity.status,
            size_bytes=entity.size_bytes,
            model_format=entity.model_format,
            tags=entity.tags,
            registered_at=entity.registered_at,
            archived_at=entity.archived_at,
        )

    def _update_model(self, model: ModelModel, entity: Model) -> None:
        """Update ORM model fields from entity."""
        model.model_name = entity.model_name
        model.owner_id = entity.owner_id
        model.version = entity.version
        model.display_name = entity.display_name
        model.description = entity.description
        model.training_job_id = entity.training_job_id
        model.checkpoint_id = entity.checkpoint_id
        model.model_uri = entity.model_uri
        model.registry_arn = entity.registry_arn
        model.registry_status = entity.registry_status
        model.metrics = entity.metrics
        model.hyperparameters = entity.hyperparameters
        model.framework = entity.framework
        model.framework_version = entity.framework_version
        model.status = entity.status
        model.size_bytes = entity.size_bytes
        model.model_format = entity.model_format
        model.tags = entity.tags
        model.registered_at = entity.registered_at
        model.archived_at = entity.archived_at

    async def get_by_id(self, model_id: int) -> Model | None:
        """Get model by ID with owner preloaded."""
        result = await self._session.execute(
            select(ModelModel)
            .options(selectinload(ModelModel.owner))
            .where(ModelModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def get_by_name_and_version(
        self, model_name: str, version: str
    ) -> Model | None:
        """Get model by name and version."""
        result = await self._session.execute(
            select(ModelModel)
            .options(selectinload(ModelModel.owner))
            .where(ModelModel.model_name == model_name, ModelModel.version == version)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

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
        if model is None:
            return None
        return self._to_entity(model)

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
        # Build base query
        query = select(ModelModel).options(selectinload(ModelModel.owner))
        count_query = select(func.count(ModelModel.id))

        # Apply filters
        if owner_id is not None:
            query = query.where(ModelModel.owner_id == owner_id)
            count_query = count_query.where(ModelModel.owner_id == owner_id)

        if training_job_id is not None:
            query = query.where(ModelModel.training_job_id == training_job_id)
            count_query = count_query.where(
                ModelModel.training_job_id == training_job_id
            )

        if status is not None:
            # Handle both string and enum
            if isinstance(status, str):
                status_enum = ModelStatus[status.upper()]
            else:
                status_enum = status
            query = query.where(ModelModel.status == status_enum)
            count_query = count_query.where(ModelModel.status == status_enum)

        if framework is not None:
            # Handle both string and enum
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
        result = await self._session.execute(
            select(ModelModel).where(ModelModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        model.status = ModelStatus.ARCHIVED
        model.archived_at = utc_now()
        model.updated_at = utc_now()
        await self._session.flush()
        return True
