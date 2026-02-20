"""Space API dependencies - 依赖注入函数."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.spaces.application.interfaces import ISageMakerSpacesClient
from src.modules.spaces.application.services import SpaceService
from src.modules.spaces.infrastructure.external import get_sagemaker_spaces_client
from src.modules.spaces.infrastructure.repositories import SpaceRepository
from src.shared.infrastructure.database import get_db


def get_sagemaker_client() -> ISageMakerSpacesClient:
    """获取 SageMaker Spaces 客户端单例."""
    return get_sagemaker_spaces_client()


async def get_space_service(
    session: AsyncSession = Depends(get_db),
    sagemaker_client: ISageMakerSpacesClient = Depends(get_sagemaker_client),
) -> SpaceService:
    """获取 SpaceService 实例."""
    space_repository = SpaceRepository(session)
    return SpaceService(
        space_repository=space_repository,
        sagemaker_client=sagemaker_client,
    )
