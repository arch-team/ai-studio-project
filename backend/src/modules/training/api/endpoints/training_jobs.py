"""Training Jobs Endpoints - CRUD 和状态操作。"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user, require_engineer
from src.modules.auth.api.permissions import (
    check_resource_owner_or_privileged,
    get_owner_filter,
)
from src.modules.training.api.dependencies import (
    get_checkpoint_service,
    get_job_template_service,
    get_training_job_service,
)
from src.modules.training.api.schemas import (
    CreateJobFromTemplateRequest,
    CreateTrainingJobRequest,
    JobPriorityEnum,
    JobStatusEnum,
    TrainingJobDetail,
    TrainingJobListResponse,
    TrainingJobSummary,
    UpdateTrainingJobRequest,
)
from src.modules.training.application.services import (
    CheckpointService,
    JobTemplateService,
    TrainingJobService,
)
from src.modules.training.domain.value_objects import JobPriority, JobStatus
from src.shared.api.pagination import (
    PageParam,
    PageSizeParam,
    SortByParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
)
from src.shared.utils import EnumMapper

router = APIRouter()


@router.post("", response_model=TrainingJobDetail, status_code=status.HTTP_201_CREATED)
async def create_training_job(
    data: CreateTrainingJobRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
) -> TrainingJobDetail:
    """Create a new training job."""
    job_data = data.model_dump(mode="json")
    job = await service.create_job(owner_id=current_user.user_id, data=job_data)
    return TrainingJobDetail.from_entity(job)


@router.get("", response_model=TrainingJobListResponse)
async def list_training_jobs(
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    status: JobStatusEnum | None = Query(default=None, description="Filter by status"),
    priority: JobPriorityEnum | None = Query(default=None, description="Filter by priority"),
    submitted_after: datetime | None = Query(default=None, description="Filter by submission date"),
    submitted_before: datetime | None = Query(default=None, description="Filter by submission date"),
    sort_by: SortByParam = "created_at",
    sort_order: SortOrderParam = SortOrder.DESC,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
) -> TrainingJobListResponse:
    """List training jobs with pagination and filters."""
    jobs, total = await service.list_jobs(
        owner_id=get_owner_filter(current_user),
        status=EnumMapper.to_domain(status, JobStatus),
        priority=EnumMapper.to_domain(priority, JobPriority),
        submitted_after=submitted_after,
        submitted_before=submitted_before,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )

    return TrainingJobListResponse(
        **build_paginated_response(
            items=[TrainingJobSummary.from_entity(job) for job in jobs],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("/from-template/{template_id}", response_model=TrainingJobDetail, status_code=status.HTTP_201_CREATED)
async def create_job_from_template(
    template_id: int,
    data: CreateJobFromTemplateRequest,
    current_user: CurrentUser = Depends(require_engineer),
    job_service: TrainingJobService = Depends(get_training_job_service),
    template_service: JobTemplateService = Depends(get_job_template_service),
) -> TrainingJobDetail:
    """Create a training job from a template.

    Uses the template's training configuration as the base,
    with optional overrides from the request body.
    """
    # Get template (also checks visibility)
    template = await template_service.get_template(template_id, current_user.user_id)

    # Build job data from template config
    config = template.training_config
    job_data = {
        "job_name": data.job_name,
        "display_name": data.display_name,
        "image_uri": config.get("image"),
        "instance_type": config.get("instance_type"),
        "node_count": data.node_count or config.get("instance_count", 1),
        "distribution_strategy": config.get("distribution_strategy", "ddp"),
        "entrypoint_command": (
            config.get("script_path", "").split() if config.get("script_path") else ["python", "train.py"]
        ),
        "environment_variables": {
            **(config.get("environment") or {}),
            **(data.environment_variables or {}),
        },
        "hyperparameters": config.get("hyperparameters"),
    }

    # Override priority if provided
    if data.priority:
        job_data["priority"] = data.priority.value

    # Create the job
    job = await job_service.create_job(owner_id=current_user.user_id, data=job_data)

    # Increment template usage count
    await template_service.increment_usage(template_id)

    return TrainingJobDetail.from_entity(job)


@router.get("/{job_id}", response_model=TrainingJobDetail)
async def get_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
    checkpoint_service: CheckpointService = Depends(get_checkpoint_service),
) -> TrainingJobDetail:
    """Get training job details by ID."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "view")
    checkpoints_count = await checkpoint_service.count_checkpoints_for_job(job_id)
    response = TrainingJobDetail.from_entity(job, checkpoints_count=checkpoints_count)
    # CE-03-09: hyperpod_job_arn is only visible to admin
    if not current_user.is_admin:
        response.hyperpod_job_arn = None
    return response


@router.put("/{job_id}", response_model=TrainingJobDetail)
async def update_training_job(
    job_id: int,
    data: UpdateTrainingJobRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
) -> TrainingJobDetail:
    """Update a training job.

    Only certain fields can be updated:
    - priority: Job scheduling priority
    - description: Job description
    - max_epochs: Maximum training epochs
    - checkpoint_interval: Checkpoint save interval
    """
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "update")
    job = await service.update_job(job_id, data.model_dump(exclude_unset=True))
    return TrainingJobDetail.from_entity(job)


@router.post("/{job_id}/pause", response_model=TrainingJobDetail)
async def pause_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
) -> TrainingJobDetail:
    """Pause a running training job."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "pause")
    job = await service.pause_job(job_id)
    return TrainingJobDetail.from_entity(job)


@router.post("/{job_id}/resume", response_model=TrainingJobDetail)
async def resume_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
) -> TrainingJobDetail:
    """Resume a paused training job."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "resume")
    job = await service.resume_job(job_id)
    return TrainingJobDetail.from_entity(job)


@router.post("/{job_id}/cancel", response_model=TrainingJobDetail)
async def cancel_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
) -> TrainingJobDetail:
    """Cancel a training job."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "cancel")
    job = await service.cancel_job(job_id)
    return TrainingJobDetail.from_entity(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
) -> None:
    """Delete a training job."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "delete")
    await service.delete_job(job_id)
    return None
