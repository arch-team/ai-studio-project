"""Audit API endpoints (T061a, T061b)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.modules.audit.application import AuditService
from src.modules.audit.domain.entities import AuditLog
from src.modules.audit.domain.value_objects import ResourceType
from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import require_admin
from src.shared.api import PageParam, PageSizeParam, build_paginated_response
from src.shared.api.pagination import SortOrder, SortOrderParam
from src.shared.domain import EntityNotFoundError
from src.shared.utils import calculate_offset

from .dependencies import get_audit_service
from .schemas import (
    AuditLogCountResponse,
    AuditLogListResponse,
    AuditLogResponse,
    CleanupResultResponse,
)

router = APIRouter()


def _to_response(log: AuditLog) -> AuditLogResponse:
    """将审计日志实体转换为响应模型."""
    return AuditLogResponse.from_entity(log)


async def _get_logs_by_user(
    service: AuditService, user_id: int, page_size: int, offset: int
) -> tuple[list[AuditLog], int]:
    """按用户 ID 获取审计日志."""
    logs = await service.get_user_audit_logs(
        user_id=user_id,
        limit=page_size,
        offset=offset,
    )
    total = await service.count_user_logs(user_id)
    return logs, total


async def _get_logs_by_resource(
    service: AuditService,
    resource_type: str,
    resource_id: str,
    page_size: int,
    offset: int,
) -> tuple[list[AuditLog], int]:
    """按资源类型和 ID 获取审计日志."""
    try:
        rt = ResourceType(resource_type)
        logs = await service.get_resource_audit_logs(
            resource_type=rt,
            resource_id=resource_id,
            limit=page_size,
            offset=offset,
        )
        total = await service.count_resource_logs(
            resource_type=rt,
            resource_id=resource_id,
        )
        return logs, total
    except ValueError:
        return [], 0


async def _get_logs_by_date_range(
    service: AuditService,
    start_date: datetime,
    end_date: datetime,
    page_size: int,
    offset: int,
) -> tuple[list[AuditLog], int]:
    """按日期范围获取审计日志."""
    logs = await service.get_audit_logs_by_date_range(
        start_date=start_date,
        end_date=end_date,
        limit=page_size,
        offset=offset,
    )
    total = await service.count_logs_by_date_range(
        start_date=start_date,
        end_date=end_date,
    )
    return logs, total


async def _get_all_logs(
    service: AuditService, page_size: int, offset: int
) -> tuple[list[AuditLog], int]:
    """获取所有审计日志."""
    logs = await service.get_audit_logs(limit=page_size, offset=offset)
    total = await service.count_total_logs()
    return logs, total


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    user_id: int | None = Query(default=None, description="用户ID过滤"),
    operation_type: str | None = Query(default=None, description="操作类型过滤"),
    resource_type: str | None = Query(default=None, description="资源类型过滤"),
    resource_id: str | None = Query(default=None, description="资源ID过滤"),
    start_date: datetime | None = Query(default=None, description="开始日期"),
    end_date: datetime | None = Query(default=None, description="结束日期"),
    sort_order: SortOrderParam = SortOrder.DESC,
    current_user: CurrentUser = Depends(require_admin),
    service: AuditService = Depends(get_audit_service),
) -> AuditLogListResponse:
    """获取审计日志 (T061a).

    支持分页、多条件过滤 (user_id, operation_type, resource_type, time_range)、排序。
    仅管理员权限。
    """
    offset = calculate_offset(page, page_size)

    # 根据过滤条件选择查询策略
    if user_id is not None:
        logs, total = await _get_logs_by_user(service, user_id, page_size, offset)
    elif resource_type is not None and resource_id is not None:
        logs, total = await _get_logs_by_resource(
            service, resource_type, resource_id, page_size, offset
        )
    elif start_date is not None and end_date is not None:
        logs, total = await _get_logs_by_date_range(
            service, start_date, end_date, page_size, offset
        )
    else:
        logs, total = await _get_all_logs(service, page_size, offset)

    # 客户端排序 (按 created_at)
    reverse = sort_order == SortOrder.DESC
    logs = sorted(logs, key=lambda x: x.created_at, reverse=reverse)

    return AuditLogListResponse(
        **build_paginated_response(
            items=[_to_response(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_log_id: int,
    service: AuditService = Depends(get_audit_service),
) -> AuditLogResponse:
    """根据ID获取指定的审计日志."""
    log = await service.get_audit_log_by_id(audit_log_id)
    if log is None:
        raise EntityNotFoundError("AuditLog", str(audit_log_id))

    return _to_response(log)


@router.get("/count/total", response_model=AuditLogCountResponse)
async def get_audit_log_count(
    service: AuditService = Depends(get_audit_service),
) -> AuditLogCountResponse:
    """获取审计日志总数."""
    count = await service.count_total_logs()
    return AuditLogCountResponse(count=count)


@router.delete("/cleanup", response_model=CleanupResultResponse)
async def cleanup_expired_logs(
    current_user: CurrentUser = Depends(require_admin),
    service: AuditService = Depends(get_audit_service),
) -> CleanupResultResponse:
    """清理过期的审计日志 (T061b).

    删除 expires_at < now 的审计日志记录。
    仅管理员权限。返回清理统计信息。
    """
    deleted_count = await service.cleanup_expired_logs()
    return CleanupResultResponse(
        deleted_count=deleted_count,
        message=f"Successfully deleted {deleted_count} expired audit logs",
    )
