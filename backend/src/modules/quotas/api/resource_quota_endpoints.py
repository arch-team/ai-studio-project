"""ResourceQuota Endpoints - CRUD operations for resource quotas (T058-T060)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import require_admin
from src.modules.quotas.api.schemas import (
    CreateResourceQuotaRequest,
    QuotaStatusEnum,
    QuotaTypeEnum,
    ResourceQuotaListResponse,
    ResourceQuotaResponse,
    UpdateResourceQuotaRequest,
)
from src.modules.quotas.application.services import ResourceQuotaService
from src.modules.quotas.domain.value_objects import QuotaStatus, QuotaType
from src.shared.api.pagination import (
    PageParam,
    PageSizeParam,
    SortByParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
)
from src.shared.utils import EnumMapper

from .dependencies import get_resource_quota_service

router = APIRouter()


@router.get("", response_model=ResourceQuotaListResponse)
async def list_resource_quotas(
    page: PageParam,
    page_size: PageSizeParam,
    quota_type: QuotaTypeEnum | None = Query(default=None, description="Filter by quota type"),
    status: QuotaStatusEnum | None = Query(default=None, description="Filter by status"),
    sort_by: SortByParam = "created_at",
    sort_order: SortOrderParam = SortOrder.DESC,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceQuotaService = Depends(get_resource_quota_service),
) -> ResourceQuotaListResponse:
    """List resource quotas (T058).

    Admin-only endpoint for listing all resource quotas.
    Supports filtering by quota_type and status, with pagination.
    """
    quotas, total = await service.list_quotas(
        quota_type=EnumMapper.to_domain(quota_type, QuotaType),
        status=EnumMapper.to_domain(status, QuotaStatus),
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )

    return ResourceQuotaListResponse(
        **build_paginated_response(
            items=[ResourceQuotaResponse.from_entity(q) for q in quotas],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("", response_model=ResourceQuotaResponse, status_code=status.HTTP_201_CREATED)
async def create_resource_quota(
    data: CreateResourceQuotaRequest,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceQuotaService = Depends(get_resource_quota_service),
) -> ResourceQuotaResponse:
    """Create a new resource quota (T059).

    Admin-only endpoint for creating new resource quotas.
    The name must be unique.
    """
    quota_data = {
        "name": data.name,
        "description": data.description,
        "quota_type": data.quota_type.value,
        "max_cpu_cores": data.max_cpu_cores,
        "max_gpu_count": data.max_gpu_count,
        "max_memory_gb": data.max_memory_gb,
        "max_concurrent_jobs": data.max_concurrent_jobs,
        "gpu_types": data.gpu_types or [],
        "created_by": current_user.user_id,
    }

    # Parse valid_until if provided
    if data.valid_until:
        quota_data["valid_until"] = datetime.fromisoformat(data.valid_until.replace("Z", "+00:00"))

    quota = await service.create_quota(quota_data)
    return ResourceQuotaResponse.from_entity(quota)


@router.get("/{quota_id}", response_model=ResourceQuotaResponse)
async def get_resource_quota(
    quota_id: int,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceQuotaService = Depends(get_resource_quota_service),
) -> ResourceQuotaResponse:
    """Get a resource quota by ID.

    Admin-only endpoint for retrieving a specific quota.
    """
    quota = await service.get_quota(quota_id)
    return ResourceQuotaResponse.from_entity(quota)


@router.put("/{quota_id}", response_model=ResourceQuotaResponse)
async def update_resource_quota(
    quota_id: int,
    data: UpdateResourceQuotaRequest,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceQuotaService = Depends(get_resource_quota_service),
) -> ResourceQuotaResponse:
    """Update a resource quota (T060).

    Admin-only endpoint for updating existing quotas.
    Supports partial updates.
    """
    # Build update data from non-None fields
    update_data: dict = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.description is not None:
        update_data["description"] = data.description
    if data.quota_type is not None:
        update_data["quota_type"] = data.quota_type.value
    if data.max_cpu_cores is not None:
        update_data["max_cpu_cores"] = data.max_cpu_cores
    if data.max_gpu_count is not None:
        update_data["max_gpu_count"] = data.max_gpu_count
    if data.max_memory_gb is not None:
        update_data["max_memory_gb"] = data.max_memory_gb
    if data.max_concurrent_jobs is not None:
        update_data["max_concurrent_jobs"] = data.max_concurrent_jobs
    if data.gpu_types is not None:
        update_data["gpu_types"] = data.gpu_types
    if data.status is not None:
        update_data["status"] = data.status.value
    if data.valid_until is not None:
        update_data["valid_until"] = datetime.fromisoformat(data.valid_until.replace("Z", "+00:00"))

    quota = await service.update_quota(quota_id, update_data)
    return ResourceQuotaResponse.from_entity(quota)


@router.delete("/{quota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource_quota(
    quota_id: int,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceQuotaService = Depends(get_resource_quota_service),
) -> None:
    """Delete a resource quota (soft delete).

    Admin-only endpoint for deleting quotas (sets status to expired).
    """
    await service.delete_quota(quota_id)
    return None
