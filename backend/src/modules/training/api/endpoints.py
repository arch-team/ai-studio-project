"""Training Jobs Endpoints - CRUD operations for training jobs."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user, require_engineer
from src.modules.auth.api.permissions import (
    check_resource_owner_or_privileged,
    get_owner_filter,
)
from src.modules.training.api.dependencies import (
    get_checkpoint_service,
    get_training_job_service,
)
from src.modules.training.api.schemas import (
    CheckpointResponse,
    CheckpointStatusEnum,
    CheckpointTypeEnum,
    CreateCheckpointRequest,
    CreateTrainingJobRequest,
    JobPriorityEnum,
    JobStatusEnum,
    StorageTierEnum,
    TrainingJobDetail,
    TrainingJobListResponse,
    TrainingJobSummary,
)
from src.modules.training.application.services import CheckpointService, TrainingJobService
from src.modules.training.domain.value_objects import JobPriority, JobStatus
from src.shared.api.pagination import (
    PageParam,
    PageSizeParam,
    SortByParam,
    SortOrder,
    SortOrderParam,
    build_paginated_response,
)
from src.shared.utils import EnumMapper, utc_now

router = APIRouter()


@router.post(
    "",
    response_model=TrainingJobDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_training_job(
    data: CreateTrainingJobRequest,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
):
    """Create a new training job."""
    job_data = data.model_dump(mode="json")
    job = await service.create_job(owner_id=current_user.user_id, data=job_data)
    return TrainingJobDetail.from_entity(job)


@router.get(
    "",
    response_model=TrainingJobListResponse,
)
async def list_training_jobs(
    page: PageParam,
    page_size: PageSizeParam,
    status: JobStatusEnum | None = Query(default=None, description="Filter by status"),
    priority: JobPriorityEnum | None = Query(default=None, description="Filter by priority"),
    submitted_after: datetime | None = Query(default=None, description="Filter by submission date"),
    submitted_before: datetime | None = Query(default=None, description="Filter by submission date"),
    sort_by: SortByParam = "created_at",
    sort_order: SortOrderParam = SortOrder.DESC,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
):
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


@router.get(
    "/{job_id}",
    response_model=TrainingJobDetail,
)
async def get_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
):
    """Get training job details by ID."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "view")
    return TrainingJobDetail.from_entity(job)


@router.post(
    "/{job_id}/pause",
    response_model=TrainingJobDetail,
)
async def pause_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
):
    """Pause a running training job."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "pause")
    job = await service.pause_job(job_id)
    return TrainingJobDetail.from_entity(job)


@router.post(
    "/{job_id}/resume",
    response_model=TrainingJobDetail,
)
async def resume_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
):
    """Resume a paused training job."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "resume")
    job = await service.resume_job(job_id)
    return TrainingJobDetail.from_entity(job)


@router.post(
    "/{job_id}/cancel",
    response_model=TrainingJobDetail,
)
async def cancel_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
):
    """Cancel a training job."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "cancel")
    job = await service.cancel_job(job_id)
    return TrainingJobDetail.from_entity(job)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
):
    """Delete a training job."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "delete")
    await service.delete_job(job_id)
    return None


# === Checkpoint Endpoints ===


@router.post(
    "/{job_id}/checkpoints",
    response_model=CheckpointResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_manual_checkpoint(
    job_id: int,
    data: CreateCheckpointRequest | None = None,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
    checkpoint_service: CheckpointService = Depends(get_checkpoint_service),
):
    """Create a manual checkpoint for a running training job."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "create checkpoints for")

    if job.status != JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot create checkpoint for job in {job.status.value} state",
        )

    checkpoint_name = (
        data.checkpoint_name
        if data and data.checkpoint_name
        else f"manual-checkpoint-{utc_now().strftime('%Y%m%d-%H%M%S')}"
    )
    storage_path = f"{job.checkpoint_mount_path or '/checkpoints'}/{job.job_name}/{checkpoint_name}.pt"

    checkpoint = await checkpoint_service.create_manual_checkpoint(
        training_job_id=job_id,
        checkpoint_name=checkpoint_name,
        storage_path=storage_path,
        epoch=job.current_epoch,
        step=job.current_step,
        loss=job.latest_loss,
        accuracy=job.latest_accuracy,
    )

    return CheckpointResponse(
        id=checkpoint.id,
        training_job_id=checkpoint.training_job_id,
        checkpoint_name=checkpoint.checkpoint_name,
        storage_path=checkpoint.storage_path,
        checkpoint_type=CheckpointTypeEnum(checkpoint.checkpoint_type.value.lower()),
        epoch=checkpoint.epoch,
        step=checkpoint.step,
        size_bytes=checkpoint.size_bytes,
        loss=checkpoint.loss,
        accuracy=checkpoint.accuracy,
        storage_tier=StorageTierEnum(checkpoint.storage_tier.value.lower()),
        status=CheckpointStatusEnum(checkpoint.status.value.lower()),
        metadata=None,
        created_at=checkpoint.created_at,
    )
