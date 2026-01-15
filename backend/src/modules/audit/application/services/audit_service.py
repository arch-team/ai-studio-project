"""Audit service - Business logic for audit log operations."""

from datetime import datetime

from src.modules.audit.domain.entities import AuditLog
from src.modules.audit.domain.repositories import IAuditLogRepository
from src.modules.audit.domain.value_objects import OperationType, ResourceType


class AuditService:
    """Service for audit log operations."""

    def __init__(self, repository: IAuditLogRepository):
        self._repository = repository

    async def get_audit_logs(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs with pagination."""
        return await self._repository.get_all(limit=limit, offset=offset)

    async def get_audit_log_by_id(self, audit_log_id: int) -> AuditLog | None:
        """Get audit log by ID."""
        from uuid import UUID

        return await self._repository.get_by_id(UUID(int=audit_log_id))

    async def get_user_audit_logs(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs for a specific user."""
        return await self._repository.get_by_user_id(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    async def get_resource_audit_logs(
        self,
        resource_type: ResourceType,
        resource_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs for a specific resource."""
        return await self._repository.get_by_resource(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
            offset=offset,
        )

    async def get_audit_logs_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs within a date range."""
        return await self._repository.get_by_date_range(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

    async def create_audit_log(self, audit_log: AuditLog) -> AuditLog:
        """Create a new audit log entry."""
        return await self._repository.add(audit_log)

    async def cleanup_expired_logs(self) -> int:
        """Delete expired audit logs. Returns count of deleted records."""
        return await self._repository.delete_expired()

    async def count_total_logs(self) -> int:
        """Get total count of audit logs."""
        return await self._repository.count_total()

    async def count_user_logs(self, user_id: int) -> int:
        """Get count of audit logs for a specific user."""
        return await self._repository.count_by_user_id(user_id)
