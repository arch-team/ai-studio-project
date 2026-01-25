"""Audit log repository implementation."""

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit.domain.entities import AuditLog
from src.modules.audit.domain.repositories import IAuditLogRepository
from src.modules.audit.domain.value_objects import (
    AuditStatus,
    OperationType,
    ResourceType,
)
from src.modules.audit.infrastructure.models import AuditLogModel
from src.modules.audit.infrastructure.models import AuditStatus as ModelAuditStatus
from src.modules.audit.infrastructure.models import OperationType as ModelOperationType
from src.modules.audit.infrastructure.models import ResourceType as ModelResourceType
from src.shared.infrastructure.repository_base import EnhancedBaseRepository
from src.shared.utils import utc_now


class AuditLogRepositoryImpl(EnhancedBaseRepository[AuditLog, AuditLogModel, int], IAuditLogRepository):
    """SQLAlchemy implementation of audit log repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLogModel)

    def _to_entity(self, model: AuditLogModel) -> AuditLog:
        """Convert ORM model to domain entity."""
        return AuditLog(
            id=model.id,
            operation_type=OperationType(model.operation_type.value),
            resource_type=ResourceType(model.resource_type.value),
            status=AuditStatus(model.status.value),
            user_id=model.user_id,
            resource_id=model.resource_id,
            request_data=model.request_data,
            response_data=model.response_data,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            created_at=model.created_at,
            expires_at=model.expires_at,
        )

    def _to_model(self, entity: AuditLog) -> AuditLogModel:
        """Convert domain entity to ORM model."""
        return AuditLogModel(
            id=entity.id if entity.id != 0 else None,
            operation_type=ModelOperationType(entity.operation_type.value),
            resource_type=ModelResourceType(entity.resource_type.value),
            status=ModelAuditStatus(entity.status.value),
            user_id=entity.user_id,
            resource_id=entity.resource_id,
            request_data=entity.request_data,
            response_data=entity.response_data,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
            created_at=entity.created_at,
            expires_at=entity.expires_at,
        )

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
        return result.rowcount

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
