"""Audit API dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit.application import AuditService
from src.modules.audit.domain.repositories import IAuditLogRepository
from src.modules.audit.infrastructure import AuditLogRepositoryImpl
from src.shared.infrastructure import get_db


async def get_audit_repository(
    session: AsyncSession = Depends(get_db),
) -> IAuditLogRepository:
    """Get audit log repository instance."""
    return AuditLogRepositoryImpl(session)


async def get_audit_service(
    repository: IAuditLogRepository = Depends(get_audit_repository),
) -> AuditService:
    """Get audit service instance."""
    return AuditService(repository)
