"""Space Service - Business logic for development space management (skeleton)."""

import uuid

from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.exceptions import DuplicateSpaceNameError
from src.modules.spaces.domain.repositories import ISpaceRepository
from src.modules.spaces.domain.value_objects import (
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.shared.application import BaseService
from src.shared.utils import utc_now


class SpaceService(BaseService[Space, str]):
    """Service for managing development spaces."""

    def __init__(
        self,
        space_repository: ISpaceRepository,
    ):
        super().__init__(space_repository, "Space")
        self._space_repository = space_repository

    async def create_space(self, owner_id: int, data: dict) -> Space:
        """Create a new development space."""
        space_name = data["space_name"]

        # Check for duplicate name for same owner
        existing = await self._space_repository.get_by_name_and_owner(space_name, owner_id)
        if existing:
            raise DuplicateSpaceNameError(space_name, owner_id)

        # Create domain entity
        space = Space(
            id=str(uuid.uuid4()),
            space_name=space_name,
            owner_id=owner_id,
            instance_type=SpaceInstanceType(data.get("instance_type", "ml.g5.xlarge")),
            space_type=SpaceType(data.get("space_type", "jupyter")),
            storage_size_gb=data.get("storage_size_gb", 20),
            status=SpaceStatus.PENDING,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        # Save to database
        return await self._space_repository.create(space)

    async def get_space(self, space_id: str) -> Space:
        """Get space by ID."""
        return await self._get_or_raise(space_id)

    async def list_spaces(
        self,
        owner_id: int | None = None,
        status: SpaceStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Space], int]:
        """List spaces with filters and pagination."""
        return await self._space_repository.list_spaces(
            owner_id=owner_id,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def start_space(self, space_id: str) -> Space:
        """Start a development space."""
        space = await self._get_or_raise(space_id)
        space.start()
        # TODO: Call SageMaker API to start space
        return await self._space_repository.update(space)

    async def stop_space(self, space_id: str) -> Space:
        """Stop a development space."""
        space = await self._get_or_raise(space_id)
        space.stop()
        # TODO: Call SageMaker API to stop space
        return await self._space_repository.update(space)

    async def delete_space(self, space_id: str) -> None:
        """Delete a development space (soft delete)."""
        space = await self._get_or_raise(space_id)
        space.delete()
        # TODO: Call SageMaker API to delete space
        await self._space_repository.soft_delete(space_id)
