"""Job Templates API Endpoints - CRUD operations for job templates."""

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user, require_engineer
from src.modules.training.api.dependencies import get_job_template_service
from src.modules.training.api.schemas import (
    CreateJobTemplateRequest,
    JobTemplateDetail,
    JobTemplateListResponse,
    JobTemplateSummary,
    UpdateJobTemplateRequest,
)
from src.modules.training.application.services import JobTemplateService
from src.shared.api.pagination import (
    PageParam,
    PageSizeParam,
    SortByParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
)

router = APIRouter()


@router.post(
    "",
    response_model=JobTemplateDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_job_template(
    data: CreateJobTemplateRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: JobTemplateService = Depends(get_job_template_service),
) -> JobTemplateDetail:
    """Create a new job template."""
    template_data = data.model_dump(mode="json")
    template = await service.create_template(
        owner_id=current_user.user_id,
        data=template_data,
    )
    return JobTemplateDetail.from_entity(template)


@router.get(
    "",
    response_model=JobTemplateListResponse,
)
async def list_job_templates(
    page: PageParam,
    page_size: PageSizeParam,
    search: str | None = Query(default=None, description="Search by name"),
    sort_by: SortByParam = "usage_count",
    sort_order: SortOrderParam = SortOrder.DESC,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: JobTemplateService = Depends(get_job_template_service),
) -> JobTemplateListResponse:
    """List job templates visible to current user."""
    templates, total = await service.list_visible_templates(
        user_id=current_user.user_id,
        search_name=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )

    return JobTemplateListResponse(
        **build_paginated_response(
            items=[JobTemplateSummary.from_entity(t) for t in templates],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get(
    "/popular",
    response_model=list[JobTemplateSummary],
)
async def get_popular_templates(
    limit: int = Query(default=10, ge=1, le=50, description="Number of templates to return"),
    service: JobTemplateService = Depends(get_job_template_service),
) -> list[JobTemplateSummary]:
    """Get most popular public templates."""
    templates = await service.get_popular_templates(limit)
    return [JobTemplateSummary.from_entity(t) for t in templates]


@router.get(
    "/{template_id}",
    response_model=JobTemplateDetail,
)
async def get_job_template(
    template_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: JobTemplateService = Depends(get_job_template_service),
) -> JobTemplateDetail:
    """Get job template details by ID."""
    template = await service.get_template(template_id, current_user.user_id)
    return JobTemplateDetail.from_entity(template)


@router.put(
    "/{template_id}",
    response_model=JobTemplateDetail,
)
async def update_job_template(
    template_id: int,
    data: UpdateJobTemplateRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: JobTemplateService = Depends(get_job_template_service),
) -> JobTemplateDetail:
    """Update a job template (owner only)."""
    update_data = data.model_dump(mode="json", exclude_unset=True)
    template = await service.update_template(
        template_id=template_id,
        user_id=current_user.user_id,
        data=update_data,
    )
    return JobTemplateDetail.from_entity(template)


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_job_template(
    template_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: JobTemplateService = Depends(get_job_template_service),
) -> None:
    """Soft delete a job template (owner only)."""
    await service.delete_template(template_id, current_user.user_id)
    return None
