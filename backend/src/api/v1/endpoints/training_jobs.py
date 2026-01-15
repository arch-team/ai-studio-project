"""Training Jobs Endpoints - CRUD operations for training jobs."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import CurrentUser
from src.api.v1.dependencies.auth import get_current_active_user, require_engineer
from src.api.v1.dependencies.permissions import (
    check_resource_owner_or_privileged,
    get_owner_filter,
)
from src.api.v1.dependencies.services import get_checkpoint_service
from src.api.v1.schemas.training_job import (
    CheckpointResponse,
    CheckpointStatusEnum,
    CheckpointTypeEnum,
    CreateCheckpointRequest,
    CreateTrainingJobRequest,
    ErrorResponse,
    JobPriorityEnum,
    JobStatusEnum,
    StorageTierEnum,
    TrainingJobDetail,
    TrainingJobListResponse,
    TrainingJobSummary,
)
from src.application.services.checkpoint_service import CheckpointService
from src.application.services.training_job_service import TrainingJobService
from src.core.database import get_db
from src.core.mapping import EnumMapper
from src.core.utils import calculate_total_pages
from src.domain.entities.training_job import JobPriority, JobStatus
from src.infrastructure.external.hyperpod.client import HyperPodClient
from src.infrastructure.persistence.repositories.training_job_repository_impl import (
    TrainingJobRepository,
)

router = APIRouter(prefix="/training-jobs", tags=["Training Jobs"])


def _to_domain_status(status: JobStatusEnum | None) -> JobStatus | None:
    """Convert API status enum to domain status."""
    if status is None:
        return None
    return EnumMapper.to_domain(status, JobStatus)


def _to_domain_priority(priority: JobPriorityEnum | None) -> JobPriority | None:
    """Convert API priority enum to domain priority."""
    if priority is None:
        return None
    return EnumMapper.to_domain(priority, JobPriority)


async def get_training_job_service(
    session: AsyncSession = Depends(get_db),
) -> TrainingJobService:
    """Dependency for TrainingJobService."""
    repository = TrainingJobRepository(session)
    hyperpod_client = HyperPodClient()
    return TrainingJobService(repository=repository, hyperpod_client=hyperpod_client)


@router.post(
    "",
    response_model=TrainingJobDetail,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Job name already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
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
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}},
)
async def list_training_jobs(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: JobStatusEnum | None = Query(default=None, description="Filter by status"),
    priority: JobPriorityEnum | None = Query(
        default=None, description="Filter by priority"
    ),
    submitted_after: datetime | None = Query(
        default=None, description="Filter by submission date (after)"
    ),
    submitted_before: datetime | None = Query(
        default=None, description="Filter by submission date (before)"
    ),
    sort_by: str = Query(default="created_at", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
):
    """List training jobs with pagination and filters."""
    jobs, total = await service.list_jobs(
        owner_id=get_owner_filter(current_user),
        status=_to_domain_status(status),
        priority=_to_domain_priority(priority),
        submitted_after=submitted_after,
        submitted_before=submitted_before,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return TrainingJobListResponse(
        items=[TrainingJobSummary.from_entity(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=calculate_total_pages(total, page_size),
    )


@router.get(
    "/{job_id}",
    response_model=TrainingJobDetail,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def get_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
):
    """Get training job details by ID."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(
        job.owner_id, current_user, "training job", "view"
    )
    return TrainingJobDetail.from_entity(job)


@router.post(
    "/{job_id}/pause",
    response_model=TrainingJobDetail,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Invalid state transition"},
    },
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
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Invalid state transition"},
    },
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
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Invalid state transition"},
    },
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
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
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
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Job not in running state"},
    },
)
async def create_manual_checkpoint(
    job_id: int,
    data: CreateCheckpointRequest | None = None,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
    checkpoint_service: CheckpointService = Depends(get_checkpoint_service),
):
    """Create a manual checkpoint for a running training job (T031d)."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(
        job.owner_id, current_user, "training job", "create checkpoints for"
    )

    # Job must be running to create a manual checkpoint
    if job.status != JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot create checkpoint for job in {job.status.value} state. "
            "Job must be running.",
        )

    # Generate checkpoint name
    checkpoint_name = (
        data.checkpoint_name
        if data and data.checkpoint_name
        else f"manual-checkpoint-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    )

    # Generate storage path
    storage_path = (
        f"{job.checkpoint_mount_path or '/checkpoints'}/"
        f"{job.job_name}/{checkpoint_name}.pt"
    )

    # Create checkpoint via CheckpointService
    checkpoint = await checkpoint_service.create_manual_checkpoint(
        training_job_id=job_id,
        checkpoint_name=checkpoint_name,
        storage_path=storage_path,
        epoch=job.current_epoch,
        step=job.current_step,
        loss=job.latest_loss,
        accuracy=job.latest_accuracy,
    )

    # TODO: In production, trigger actual checkpoint save via HyperPod signal
    # This would involve sending a signal to the training pods to save state

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
