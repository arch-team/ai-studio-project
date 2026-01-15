"""Quotas API dependencies - Dependency injection for services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database import get_db
from src.modules.quotas.application.services import ResourceLimitConfigService
from src.modules.quotas.infrastructure.repositories import ResourceLimitConfigRepository


async def get_resource_limit_config_service(
    session: AsyncSession = Depends(get_db),
) -> ResourceLimitConfigService:
    """Dependency for ResourceLimitConfigService."""
    repository = ResourceLimitConfigRepository(session)
    return ResourceLimitConfigService(repository=repository)
