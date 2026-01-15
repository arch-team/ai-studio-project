"""Audit API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.modules.audit.application import AuditService
from src.modules.audit.domain.value_objects import OperationType, ResourceType
from src.shared.utils import calculate_offset, calculate_total_pages

from .dependencies import get_audit_service
from .schemas import (
    AuditLogCountResponse,
    AuditLogListResponse,
    AuditLogResponse,
    CleanupResultResponse,
)

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    user_id: int | None = Query(default=None, description="用户ID过滤"),
    resource_type: str | None = Query(default=None, description="资源类型过滤"),
    resource_id: str | None = Query(default=None, description="资源ID过滤"),
    start_date: datetime | None = Query(default=None, description="开始日期"),
    end_date: datetime | None = Query(default=None, description="结束日期"),
    service: AuditService = Depends(get_audit_service),
) -> AuditLogListResponse:
    """Get audit logs with optional filtering."""
    offset = calculate_offset(page, page_size)

    # Apply filters based on provided parameters
    if user_id is not None:
        logs = await service.get_user_audit_logs(
            user_id=user_id,
            limit=page_size,
            offset=offset,
        )
        total = await service.count_user_logs(user_id)
    elif resource_type is not None and resource_id is not None:
        try:
            rt = ResourceType(resource_type)
            logs = await service.get_resource_audit_logs(
                resource_type=rt,
                resource_id=resource_id,
                limit=page_size,
                offset=offset,
            )
            total = len(logs)  # TODO: Add count method for resources
        except ValueError:
            logs = []
            total = 0
    elif start_date is not None and end_date is not None:
        logs = await service.get_audit_logs_by_date_range(
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=offset,
        )
        total = len(logs)  # TODO: Add count method for date range
    else:
        logs = await service.get_audit_logs(limit=page_size, offset=offset)
        total = await service.count_total_logs()

    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=log.id,
                operation_type=log.operation_type.value,
                resource_type=log.resource_type.value,
                status=log.status.value,
                user_id=log.user_id,
                resource_id=log.resource_id,
                request_data=log.request_data,
                response_data=log.response_data,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
                expires_at=log.expires_at,
            )
            for log in logs
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=calculate_total_pages(total, page_size),
    )


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_log_id: int,
    service: AuditService = Depends(get_audit_service),
) -> AuditLogResponse:
    """Get a specific audit log by ID."""
    from src.shared.domain import EntityNotFoundError

    log = await service.get_audit_log_by_id(audit_log_id)
    if log is None:
        raise EntityNotFoundError("AuditLog", str(audit_log_id))

    return AuditLogResponse(
        id=log.id,
        operation_type=log.operation_type.value,
        resource_type=log.resource_type.value,
        status=log.status.value,
        user_id=log.user_id,
        resource_id=log.resource_id,
        request_data=log.request_data,
        response_data=log.response_data,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        created_at=log.created_at,
        expires_at=log.expires_at,
    )


@router.get("/count/total", response_model=AuditLogCountResponse)
async def get_audit_log_count(
    service: AuditService = Depends(get_audit_service),
) -> AuditLogCountResponse:
    """Get total count of audit logs."""
    count = await service.count_total_logs()
    return AuditLogCountResponse(count=count)


@router.delete("/expired", response_model=CleanupResultResponse)
async def cleanup_expired_logs(
    service: AuditService = Depends(get_audit_service),
) -> CleanupResultResponse:
    """Delete expired audit logs (admin only)."""
    # TODO: Add admin permission check
    deleted_count = await service.cleanup_expired_logs()
    return CleanupResultResponse(
        deleted_count=deleted_count,
        message=f"Successfully deleted {deleted_count} expired audit logs",
    )
