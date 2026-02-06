"""Audit log repository implementation."""

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import PydanticRepository
from src.shared.utils import utc_now

from ...domain.entities import AuditLog
from ...domain.repositories import IAuditLogRepository
from ...domain.value_objects import OperationType, ResourceType
from ..models import AuditLogModel
from ..models import OperationType as ModelOperationType
from ..models import ResourceType as ModelResourceType


class AuditLogRepositoryImpl(PydanticRepository[AuditLog, AuditLogModel, int], IAuditLogRepository):
    """SQLAlchemy implementation of audit log repository."""

    _entity_class = AuditLog
    _updatable_fields: list[str] = []  # Audit logs are immutable

    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLogModel)

    # ========== IAuditLogRepository 基础方法 ==========

    async def add(self, entity: AuditLog) -> AuditLog:
        """Add new audit log entry (alias for create)."""
        return await self.create(entity)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        """Get all audit logs with pagination."""
        result = await self._session.execute(
            select(AuditLogModel).order_by(AuditLogModel.created_at.desc()).limit(limit).offset(offset)
        )
        return [self._to_entity(model) for model in result.scalars()]

    # ========== IAuditLogRepository 接口方法 ==========

    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs by user ID."""
        result = await self._session.execute(
            select(AuditLogModel)
            .where(AuditLogModel.user_id == user_id)
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(model) for model in result.scalars()]

    async def get_by_resource(
        self,
        resource_type: ResourceType,
        resource_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs by resource type and ID."""
        result = await self._session.execute(
            select(AuditLogModel)
            .where(
                AuditLogModel.resource_type == ModelResourceType(resource_type.value),
                AuditLogModel.resource_id == resource_id,
            )
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(model) for model in result.scalars()]

    async def get_by_operation_type(
        self,
        operation_type: OperationType,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs by operation type."""
        result = await self._session.execute(
            select(AuditLogModel)
            .where(AuditLogModel.operation_type == ModelOperationType(operation_type.value))
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(model) for model in result.scalars()]

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs within a date range."""
        result = await self._session.execute(
            select(AuditLogModel)
            .where(
                AuditLogModel.created_at >= start_date,
                AuditLogModel.created_at <= end_date,
            )
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(model) for model in result.scalars()]

    async def delete_expired(self) -> int:
        """Delete expired audit logs."""
        result = await self._session.execute(delete(AuditLogModel).where(AuditLogModel.expires_at < utc_now()))
        return int(result.rowcount) if result.rowcount else 0

    async def count_by_user_id(self, user_id: int) -> int:
        """Count audit logs for a specific user."""
        result = await self._session.execute(select(func.count()).where(AuditLogModel.user_id == user_id))
        return result.scalar() or 0

    async def count_by_resource(
        self,
        resource_type: ResourceType,
        resource_id: str,
    ) -> int:
        """Count audit logs for a specific resource."""
        result = await self._session.execute(
            select(func.count()).where(
                AuditLogModel.resource_type == ModelResourceType(resource_type.value),
                AuditLogModel.resource_id == resource_id,
            )
        )
        return result.scalar() or 0

    async def count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count audit logs within a date range."""
        result = await self._session.execute(
            select(func.count()).where(
                AuditLogModel.created_at >= start_date,
                AuditLogModel.created_at <= end_date,
            )
        )
        return result.scalar() or 0

    async def count_total(self) -> int:
        """Count total audit logs."""
        result = await self._session.execute(select(func.count()).select_from(AuditLogModel))
        return result.scalar() or 0
