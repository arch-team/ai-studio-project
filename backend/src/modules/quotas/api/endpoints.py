"""ResourceLimitConfig Endpoints - Admin CRUD operations for resource limits."""

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import require_admin
from src.modules.quotas.api.dependencies import get_resource_limit_config_service
from src.modules.quotas.api.schemas import (
    CreateResourceLimitConfigRequest,
    LimitRoleEnum,
    ResourceLimitConfigListResponse,
    ResourceLimitConfigResponse,
    UpdateResourceLimitConfigRequest,
)
from src.modules.quotas.application.services import ResourceLimitConfigService
from src.modules.quotas.domain.value_objects import LimitRole
from src.shared.utils import EnumMapper, calculate_total_pages

router = APIRouter()


@router.get(
    "",
    response_model=ResourceLimitConfigListResponse,
)
async def list_resource_limit_configs(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    role: LimitRoleEnum | None = Query(default=None, description="Filter by role"),
    project_id: int | None = Query(default=None, description="Filter by project ID"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)"),
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceLimitConfigService = Depends(get_resource_limit_config_service),
):
    """List resource limit configurations.

    Admin-only endpoint for listing all resource limit configurations.
    Supports filtering by role and project_id, with pagination.
    """
    configs, total = await service.list_configs(
        role=EnumMapper.to_domain(role, LimitRole),
        project_id=project_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return ResourceLimitConfigListResponse(
        items=[ResourceLimitConfigResponse.from_entity(c) for c in configs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=calculate_total_pages(total, page_size),
    )


@router.post(
    "",
    response_model=ResourceLimitConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_resource_limit_config(
    data: CreateResourceLimitConfigRequest,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceLimitConfigService = Depends(get_resource_limit_config_service),
):
    """Create a new resource limit configuration.

    Admin-only endpoint for creating new resource limit configurations.
    The (role, project_id) combination must be unique.
    """
    config_data = {
        "config_name": data.config_name,
        "role": data.role.value,
        "project_id": data.project_id,
        "max_gpu_per_job": data.max_gpu_per_job,
        "max_cpu_per_job": data.max_cpu_per_job,
        "max_memory_gb_per_job": data.max_memory_gb_per_job,
        "max_storage_gb_per_job": data.max_storage_gb_per_job,
        "max_nodes_per_job": data.max_nodes_per_job,
        "priority_default": data.priority_default.value,
    }

    config = await service.create_config(config_data)
    return ResourceLimitConfigResponse.from_entity(config)


@router.get(
    "/{config_id}",
    response_model=ResourceLimitConfigResponse,
)
async def get_resource_limit_config(
    config_id: int,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceLimitConfigService = Depends(get_resource_limit_config_service),
):
    """Get a resource limit configuration by ID.

    Admin-only endpoint for retrieving a specific configuration.
    """
    config = await service.get_config(config_id)
    return ResourceLimitConfigResponse.from_entity(config)


@router.put(
    "/{config_id}",
    response_model=ResourceLimitConfigResponse,
)
async def update_resource_limit_config(
    config_id: int,
    data: UpdateResourceLimitConfigRequest,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceLimitConfigService = Depends(get_resource_limit_config_service),
):
    """Update a resource limit configuration.

    Admin-only endpoint for updating existing configurations.
    Supports partial updates.
    """
    # Build update data from non-None fields
    update_data = {}
    if data.config_name is not None:
        update_data["config_name"] = data.config_name
    if data.role is not None:
        update_data["role"] = data.role.value
    if data.project_id is not None:
        update_data["project_id"] = data.project_id
    if data.max_gpu_per_job is not None:
        update_data["max_gpu_per_job"] = data.max_gpu_per_job
    if data.max_cpu_per_job is not None:
        update_data["max_cpu_per_job"] = data.max_cpu_per_job
    if data.max_memory_gb_per_job is not None:
        update_data["max_memory_gb_per_job"] = data.max_memory_gb_per_job
    if data.max_storage_gb_per_job is not None:
        update_data["max_storage_gb_per_job"] = data.max_storage_gb_per_job
    if data.max_nodes_per_job is not None:
        update_data["max_nodes_per_job"] = data.max_nodes_per_job
    if data.priority_default is not None:
        update_data["priority_default"] = data.priority_default.value

    config = await service.update_config(config_id, update_data)
    return ResourceLimitConfigResponse.from_entity(config)


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_resource_limit_config(
    config_id: int,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceLimitConfigService = Depends(get_resource_limit_config_service),
):
    """Delete a resource limit configuration.

    Admin-only endpoint for deleting configurations (soft delete).
    """
    await service.delete_config(config_id)
    return None
