"""Dataset API dependencies - Dependency injection for services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.datasets.application.services import DatasetService
from src.modules.datasets.domain.repositories import IDatasetRepository
from src.modules.datasets.infrastructure.repositories import DatasetRepositoryImpl
from src.shared.infrastructure import get_db


async def get_dataset_repository(
    session: AsyncSession = Depends(get_db),
) -> IDatasetRepository:
    """Dependency for IDatasetRepository."""
    return DatasetRepositoryImpl(session)


async def get_dataset_service(
    session: AsyncSession = Depends(get_db),
) -> DatasetService:
    """Dependency for DatasetService."""
    repository = DatasetRepositoryImpl(session)
    return DatasetService(repository=repository)
