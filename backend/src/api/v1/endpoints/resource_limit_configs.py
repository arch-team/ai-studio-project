"""ResourceLimitConfig Endpoints - Admin CRUD operations for resource limits."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import CurrentUser
from src.api.v1.dependencies.auth import require_admin
from src.api.v1.schemas.resource_limit_config import (
    CreateResourceLimitConfigRequest,
    ErrorResponse,
    LimitRoleEnum,
    PriorityDefaultEnum,
    ResourceLimitConfigListResponse,
    ResourceLimitConfigResponse,
    UpdateResourceLimitConfigRequest,
)
from src.application.services.resource_limit_config_service import (
    ResourceLimitConfigService,
)
from src.core.database import get_db
from src.domain.entities.resource_limit_config import LimitRole
from src.domain.exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.persistence.repositories.resource_limit_config_repository_impl import (
    ResourceLimitConfigRepository,
)

router = APIRouter(prefix="/resource-limit-configs", tags=["Resource Limit Configs"])


async def get_resource_limit_config_service(
    session: AsyncSession = Depends(get_db),
) -> ResourceLimitConfigService:
    """Dependency for ResourceLimitConfigService."""
    repository = ResourceLimitConfigRepository(session)
    return ResourceLimitConfigService(repository=repository)


def _map_role_enum(role: LimitRoleEnum | None) -> LimitRole | None:
    """Map API role enum to domain role."""
    if role is None:
        return None
    role_map = {
        LimitRoleEnum.ADMIN: LimitRole.ADMIN,
        LimitRoleEnum.PROJECT_MANAGER: LimitRole.PROJECT_MANAGER,
        LimitRoleEnum.ENGINEER: LimitRole.ENGINEER,
        LimitRoleEnum.VIEWER: LimitRole.VIEWER,
    }
    return role_map.get(role)


def _config_to_response(config) -> ResourceLimitConfigResponse:
    """Convert domain entity to response."""
    return ResourceLimitConfigResponse(
        id=config.id,
        config_name=config.config_name,
        role=LimitRoleEnum(config.role.value),
        project_id=config.project_id,
        max_gpu_per_job=config.max_gpu_per_job,
        max_cpu_per_job=config.max_cpu_per_job,
        max_memory_gb_per_job=config.max_memory_gb_per_job,
        max_storage_gb_per_job=config.max_storage_gb_per_job,
        max_nodes_per_job=config.max_nodes_per_job,
        priority_default=PriorityDefaultEnum(config.priority_default.value),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get(
    "",
    response_model=ResourceLimitConfigListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Admin only"},
    },
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
    """List resource limit configurations (T012c).

    Admin-only endpoint for listing all resource limit configurations.
    Supports filtering by role and project_id, with pagination.
    """
    configs, total = await service.list_configs(
        role=_map_role_enum(role),
        project_id=project_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ResourceLimitConfigListResponse(
        items=[_config_to_response(c) for c in configs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=ResourceLimitConfigResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Admin only"},
        409: {"model": ErrorResponse, "description": "Duplicate config"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def create_resource_limit_config(
    data: CreateResourceLimitConfigRequest,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceLimitConfigService = Depends(get_resource_limit_config_service),
):
    """Create a new resource limit configuration (T012d).

    Admin-only endpoint for creating new resource limit configurations.
    The (role, project_id) combination must be unique.
    """
    try:
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
        return _config_to_response(config)

    except DuplicateEntityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/{config_id}",
    response_model=ResourceLimitConfigResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Admin only"},
        404: {"model": ErrorResponse, "description": "Config not found"},
    },
)
async def get_resource_limit_config(
    config_id: int,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceLimitConfigService = Depends(get_resource_limit_config_service),
):
    """Get a resource limit configuration by ID.

    Admin-only endpoint for retrieving a specific configuration.
    """
    try:
        config = await service.get_config(config_id)
        return _config_to_response(config)

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResourceLimitConfig with id {config_id} not found",
        )


@router.put(
    "/{config_id}",
    response_model=ResourceLimitConfigResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Admin only"},
        404: {"model": ErrorResponse, "description": "Config not found"},
        409: {"model": ErrorResponse, "description": "Duplicate config"},
    },
)
async def update_resource_limit_config(
    config_id: int,
    data: UpdateResourceLimitConfigRequest,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceLimitConfigService = Depends(get_resource_limit_config_service),
):
    """Update a resource limit configuration (T012e).

    Admin-only endpoint for updating existing configurations.
    Supports partial updates. Changes are recorded in audit logs.
    """
    try:
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
        return _config_to_response(config)

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResourceLimitConfig with id {config_id} not found",
        )
    except DuplicateEntityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Admin only"},
        404: {"model": ErrorResponse, "description": "Config not found"},
    },
)
async def delete_resource_limit_config(
    config_id: int,
    current_user: CurrentUser = Depends(require_admin),
    service: ResourceLimitConfigService = Depends(get_resource_limit_config_service),
):
    """Delete a resource limit configuration (T012f).

    Admin-only endpoint for deleting configurations (soft delete).
    Deletion is recorded in audit logs.
    """
    try:
        await service.delete_config(config_id)
        return None

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResourceLimitConfig with id {config_id} not found",
        )
