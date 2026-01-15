"""Space Repository Implementation - SQLAlchemy data access."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.repositories import ISpaceRepository
from src.modules.spaces.domain.value_objects import SpaceStatus
from src.modules.spaces.infrastructure.models import DevelopmentSpaceModel


class SpaceRepository(ISpaceRepository):
    """SQLAlchemy implementation of space repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _model_to_entity(self, model: DevelopmentSpaceModel) -> Space:
        """Convert ORM model to domain entity."""
        return Space(
            id=model.id,
            space_name=model.space_name,
            owner_id=model.owner_id,
            instance_type=model.instance_type,
            space_type=model.space_type,
            storage_size_gb=model.storage_size_gb,
            status=model.status,
            lifecycle_config_arn=model.lifecycle_config_arn,
            sagemaker_space_arn=model.sagemaker_space_arn,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def _entity_to_model(self, entity: Space) -> DevelopmentSpaceModel:
        """Convert domain entity to ORM model."""
        return DevelopmentSpaceModel(
            id=entity.id if entity.id else str(uuid.uuid4()),
            space_name=entity.space_name,
            owner_id=entity.owner_id,
            instance_type=entity.instance_type,
            space_type=entity.space_type,
            storage_size_gb=entity.storage_size_gb,
            status=entity.status,
            lifecycle_config_arn=entity.lifecycle_config_arn,
            sagemaker_space_arn=entity.sagemaker_space_arn,
        )

    async def get_by_id(self, space_id: str) -> Space | None:
        """Get space by ID."""
        result = await self._session.execute(
            select(DevelopmentSpaceModel)
            .options(selectinload(DevelopmentSpaceModel.owner))
            .where(
                DevelopmentSpaceModel.id == space_id,
                DevelopmentSpaceModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_name_and_owner(
        self, space_name: str, owner_id: int
    ) -> Space | None:
        """Get space by name and owner ID."""
        result = await self._session.execute(
            select(DevelopmentSpaceModel)
            .options(selectinload(DevelopmentSpaceModel.owner))
            .where(
                DevelopmentSpaceModel.space_name == space_name,
                DevelopmentSpaceModel.owner_id == owner_id,
                DevelopmentSpaceModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_spaces(
        self,
        owner_id: int | None = None,
        status: SpaceStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Space], int]:
        """List spaces with pagination and filters."""
        # Build base query (exclude soft-deleted)
        query = select(DevelopmentSpaceModel).options(
            selectinload(DevelopmentSpaceModel.owner)
        ).where(DevelopmentSpaceModel.deleted_at.is_(None))
        count_query = select(func.count(DevelopmentSpaceModel.id)).where(
            DevelopmentSpaceModel.deleted_at.is_(None)
        )

        # Apply filters
        if owner_id is not None:
            query = query.where(DevelopmentSpaceModel.owner_id == owner_id)
            count_query = count_query.where(DevelopmentSpaceModel.owner_id == owner_id)

        if status is not None:
            query = query.where(DevelopmentSpaceModel.status == status)
            count_query = count_query.where(DevelopmentSpaceModel.status == status)

        # Get total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(DevelopmentSpaceModel, sort_by, DevelopmentSpaceModel.created_at)
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

    async def create(self, space: Space) -> Space:
        """Create a new space."""
        db_model = self._entity_to_model(space)
        self._session.add(db_model)
        await self._session.flush()
        await self._session.refresh(db_model)
        return self._model_to_entity(db_model)

    async def update(self, space: Space) -> Space:
        """Update an existing space."""
        result = await self._session.execute(
            select(DevelopmentSpaceModel).where(DevelopmentSpaceModel.id == space.id)
        )
        db_model = result.scalar_one_or_none()
        if db_model is None:
            raise ValueError(f"Space with id {space.id} not found")

        # Update fields
        db_model.space_name = space.space_name
        db_model.instance_type = space.instance_type
        db_model.space_type = space.space_type
        db_model.storage_size_gb = space.storage_size_gb
        db_model.status = space.status
        db_model.lifecycle_config_arn = space.lifecycle_config_arn
        db_model.sagemaker_space_arn = space.sagemaker_space_arn
        db_model.updated_at = datetime.utcnow()

        await self._session.flush()
        await self._session.refresh(db_model)
        return self._model_to_entity(db_model)

    async def soft_delete(self, space_id: str) -> bool:
        """Soft delete a space."""
        result = await self._session.execute(
            select(DevelopmentSpaceModel).where(DevelopmentSpaceModel.id == space_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        model.status = SpaceStatus.DELETED
        model.deleted_at = datetime.utcnow()
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        return True
