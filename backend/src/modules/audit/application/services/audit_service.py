"""审计服务 - 审计日志操作的业务逻辑."""

from datetime import datetime

from src.modules.audit.domain.entities import AuditLog
from src.modules.audit.domain.repositories import IAuditLogRepository
from src.modules.audit.domain.value_objects import ResourceType


class AuditService:
    """审计日志操作服务."""

    def __init__(self, repository: IAuditLogRepository):
        self._repository = repository

    async def get_audit_logs(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """获取审计日志（分页）."""
        return await self._repository.get_all(limit=limit, offset=offset)

    async def get_audit_log_by_id(self, audit_log_id: int) -> AuditLog | None:
        """根据ID获取审计日志."""
        return await self._repository.get_by_id(audit_log_id)

    async def get_user_audit_logs(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """获取指定用户的审计日志."""
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
        """获取指定资源的审计日志."""
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
        """获取日期范围内的审计日志."""
        return await self._repository.get_by_date_range(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

    async def create_audit_log(self, audit_log: AuditLog) -> AuditLog:
        """创建新的审计日志条目."""
        return await self._repository.add(audit_log)

    async def cleanup_expired_logs(self) -> int:
        """删除过期的审计日志. 返回删除的记录数."""
        return await self._repository.delete_expired()

    async def count_total_logs(self) -> int:
        """获取审计日志总数."""
        return await self._repository.count_total()

    async def count_user_logs(self, user_id: int) -> int:
        """获取指定用户的审计日志数量."""
        return await self._repository.count_by_user_id(user_id)

    async def count_resource_logs(
        self,
        resource_type: ResourceType,
        resource_id: str,
    ) -> int:
        """获取指定资源的审计日志数量."""
        return await self._repository.count_by_resource(
            resource_type=resource_type,
            resource_id=resource_id,
        )

    async def count_logs_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """获取日期范围内的审计日志数量."""
        return await self._repository.count_by_date_range(
            start_date=start_date,
            end_date=end_date,
        )
