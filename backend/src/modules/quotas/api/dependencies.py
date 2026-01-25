"""Quotas API dependencies - Dependency injection for services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.quotas.application.services import (
    ResourceLimitConfigService,
    ResourceQuotaService,
)
from src.modules.quotas.infrastructure.repositories import (
    ResourceLimitConfigRepository,
    ResourceQuotaRepository,
)
from src.shared.infrastructure.database import get_db


async def get_resource_limit_config_service(
    session: AsyncSession = Depends(get_db),
) -> ResourceLimitConfigService:
    """Dependency for ResourceLimitConfigService."""
    repository = ResourceLimitConfigRepository(session)
    return ResourceLimitConfigService(repository=repository)


async def get_resource_quota_service(
    session: AsyncSession = Depends(get_db),
) -> ResourceQuotaService:
    """Dependency for ResourceQuotaService (T058-T060)."""
    repository = ResourceQuotaRepository(session)
    return ResourceQuotaService(repository=repository)
