"""Space Repository Implementation - SQLAlchemy data access."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.repositories import ISpaceRepository
from src.modules.spaces.domain.value_objects import SpaceStatus
from src.modules.spaces.infrastructure.models import DevelopmentSpaceModel
from src.shared.infrastructure.repository_base import EnhancedBaseRepository
from src.shared.utils import utc_now


class SpaceRepository(
    EnhancedBaseRepository[Space, DevelopmentSpaceModel, str],
    ISpaceRepository,
):
    """SQLAlchemy implementation of space repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DevelopmentSpaceModel)

    def _to_entity(self, model: DevelopmentSpaceModel) -> Space:
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

    def _to_model(self, entity: Space) -> DevelopmentSpaceModel:
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

    def _update_model(self, model: DevelopmentSpaceModel, entity: Space) -> None:
        """Update ORM model fields from entity."""
        model.space_name = entity.space_name
        model.instance_type = entity.instance_type
        model.space_type = entity.space_type
        model.storage_size_gb = entity.storage_size_gb
        model.status = entity.status
        model.lifecycle_config_arn = entity.lifecycle_config_arn
        model.sagemaker_space_arn = entity.sagemaker_space_arn

    # ========== Domain-specific queries ==========

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
        return self._to_entity(model)

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
        return self._to_entity(model)

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
        filters = {}
        if owner_id is not None:
            filters["owner_id"] = owner_id
        if status is not None:
            filters["status"] = status

        return await self._list_with_filters(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

