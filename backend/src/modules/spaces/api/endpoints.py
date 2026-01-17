"""Spaces Endpoints - CRUD operations for development spaces (skeleton)."""

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user, require_engineer
from src.modules.auth.api.permissions import (
    check_resource_owner_or_privileged,
    get_owner_filter,
)
from src.modules.spaces.api.dependencies import get_space_service
from src.modules.spaces.api.schemas import (
    CreateSpaceRequest,
    SpaceDetail,
    SpaceErrorResponse,
    SpaceListResponse,
    SpaceStatusEnum,
    SpaceSummary,
)
from src.modules.spaces.application.services import SpaceService
from src.modules.spaces.domain.value_objects import SpaceStatus
from src.shared.utils import calculate_total_pages

router = APIRouter()


@router.post(
    "",
    response_model=SpaceDetail,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": SpaceErrorResponse, "description": "Space name already exists"},
        422: {"model": SpaceErrorResponse, "description": "Validation error"},
    },
)
async def create_space(
    data: CreateSpaceRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: SpaceService = Depends(get_space_service),
):
    """Create a new development space."""
    space_data = data.model_dump(mode="json")
    space = await service.create_space(owner_id=current_user.user_id, data=space_data)
    return SpaceDetail.from_entity(space)


@router.get(
    "",
    response_model=SpaceListResponse,
    responses={401: {"model": SpaceErrorResponse, "description": "Unauthorized"}},
)
async def list_spaces(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: SpaceStatusEnum | None = Query(default=None, alias="status", description="Filter by status"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: SpaceService = Depends(get_space_service),
):
    """List development spaces with pagination and filters."""
    status_domain = SpaceStatus(status_filter.value) if status_filter else None

    spaces, total = await service.list_spaces(
        owner_id=get_owner_filter(current_user),
        status=status_domain,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return SpaceListResponse(
        items=[SpaceSummary.from_entity(space) for space in spaces],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=calculate_total_pages(total, page_size),
    )


@router.get(
    "/{space_id}",
    response_model=SpaceDetail,
    responses={
        404: {"model": SpaceErrorResponse, "description": "Space not found"},
    },
)
async def get_space(
    space_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: SpaceService = Depends(get_space_service),
):
    """Get development space details by ID."""
    space = await service.get_space(space_id)
    check_resource_owner_or_privileged(space.owner_id, current_user, "space", "view")
    return SpaceDetail.from_entity(space)


@router.post(
    "/{space_id}/start",
    response_model=SpaceDetail,
    responses={
        404: {"model": SpaceErrorResponse, "description": "Space not found"},
        409: {"model": SpaceErrorResponse, "description": "Invalid state transition"},
    },
)
async def start_space(
    space_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    service: SpaceService = Depends(get_space_service),
):
    """Start a development space."""
    space = await service.get_space(space_id)
    check_resource_owner_or_privileged(space.owner_id, current_user, "space", "start")
    space = await service.start_space(space_id)
    return SpaceDetail.from_entity(space)


@router.post(
    "/{space_id}/stop",
    response_model=SpaceDetail,
    responses={
        404: {"model": SpaceErrorResponse, "description": "Space not found"},
        409: {"model": SpaceErrorResponse, "description": "Invalid state transition"},
    },
)
async def stop_space(
    space_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    service: SpaceService = Depends(get_space_service),
):
    """Stop a development space."""
    space = await service.get_space(space_id)
    check_resource_owner_or_privileged(space.owner_id, current_user, "space", "stop")
    space = await service.stop_space(space_id)
    return SpaceDetail.from_entity(space)


@router.delete(
    "/{space_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": SpaceErrorResponse, "description": "Space not found"},
        409: {"model": SpaceErrorResponse, "description": "Invalid state transition"},
    },
)
async def delete_space(
    space_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    service: SpaceService = Depends(get_space_service),
):
    """Delete a development space."""
    space = await service.get_space(space_id)
    check_resource_owner_or_privileged(space.owner_id, current_user, "space", "delete")
    await service.delete_space(space_id)
    return None
