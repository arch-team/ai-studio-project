"""Space Repository Implementation - SQLAlchemy data access."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.infrastructure import PydanticRepository

from ...domain.entities import Space
from ...domain.repositories import ISpaceRepository
from ...domain.value_objects import SpaceStatus
from ..models import DevelopmentSpaceModel


class SpaceRepository(
    PydanticRepository[Space, DevelopmentSpaceModel, str],
    ISpaceRepository,
):
    """SQLAlchemy implementation of space repository."""

    _entity_class = Space
    _updatable_fields = [
        "space_name",
        "instance_type",
        "space_type",
        "storage_size_gb",
        "status",
        "lifecycle_config_arn",
        "sagemaker_space_arn",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, DevelopmentSpaceModel)

    def _to_model(self, entity: Space) -> DevelopmentSpaceModel:
        """Override to handle UUID generation for new entities.

        convert_enums=False: 数据库枚举列以名称 (如 ML_T3_MEDIUM) 持久化，
        必须传枚举对象由 SQLAlchemy 按 .name 写入；若转为值 (ml.t3.medium)
        会因不匹配列定义而写入失败。
        """
        data = entity.to_model_dict(
            exclude={"id"} if entity.id is None else None,
            convert_enums=False,
        )
        if entity.id is None:
            data["id"] = str(uuid.uuid4())
        return self._model_class(**data)

    # ========== ISpaceRepository 接口方法 ==========

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
        return self._to_entity(model) if model else None

    async def get_by_name_and_owner(self, space_name: str, owner_id: int) -> Space | None:
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
        return self._to_entity(model) if model else None

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
        filters: dict[str, int | SpaceStatus] = {}
        if owner_id is not None:
            filters["owner_id"] = owner_id
        if status is not None:
            filters["status"] = status

        return await self.list_with_filters(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
