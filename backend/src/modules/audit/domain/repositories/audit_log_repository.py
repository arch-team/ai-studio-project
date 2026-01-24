"""Audit log repository interface."""

from abc import abstractmethod
from datetime import datetime

from src.shared.domain import IRepository

from ..entities import AuditLog
from ..value_objects import OperationType, ResourceType


class IAuditLogRepository(IRepository[AuditLog]):
    """Repository interface for audit log operations."""

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs by user ID."""

    @abstractmethod
    async def get_by_resource(
        self,
        resource_type: ResourceType,
        resource_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs by resource type and ID."""

    @abstractmethod
    async def get_by_operation_type(
        self,
        operation_type: OperationType,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs by operation type."""

    @abstractmethod
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs within a date range."""

    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete expired audit logs. Returns count of deleted records."""

    @abstractmethod
    async def count_by_user_id(self, user_id: int) -> int:
        """Count audit logs for a specific user."""

    @abstractmethod
    async def count_by_resource(
        self,
        resource_type: ResourceType,
        resource_id: str,
    ) -> int:
        """Count audit logs for a specific resource."""

    @abstractmethod
    async def count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count audit logs within a date range."""

    @abstractmethod
    async def count_total(self) -> int:
        """Count total audit logs."""
