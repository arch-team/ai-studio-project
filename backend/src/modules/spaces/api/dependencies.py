"""Space API dependencies - Dependency injection for services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database import get_db
from src.modules.spaces.application.services import SpaceService
from src.modules.spaces.infrastructure.repositories import SpaceRepository


async def get_space_service(
    session: AsyncSession = Depends(get_db),
) -> SpaceService:
    """Dependency for SpaceService."""
    space_repository = SpaceRepository(session)
    return SpaceService(
        space_repository=space_repository,
    )
