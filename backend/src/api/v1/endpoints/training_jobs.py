"""Training Jobs Endpoints - CRUD operations for training jobs."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import CurrentUser
from src.api.v1.dependencies.auth import get_current_active_user, require_engineer
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
from src.domain.entities.training_job import JobPriority, JobStatus
from src.infrastructure.external.hyperpod.client import HyperPodClient
from src.infrastructure.persistence.repositories.training_job_repository_impl import (
    TrainingJobRepository,
)

router = APIRouter(prefix="/training-jobs", tags=["Training Jobs"])


async def get_training_job_service(
    session: AsyncSession = Depends(get_db),
) -> TrainingJobService:
    """Dependency for TrainingJobService."""
    repository = TrainingJobRepository(session)
    hyperpod_client = HyperPodClient()
    return TrainingJobService(repository=repository, hyperpod_client=hyperpod_client)


def _map_status_enum(status: JobStatusEnum | None) -> JobStatus | None:
    """Map API status enum to domain status."""
    if status is None:
        return None
    status_map = {
        JobStatusEnum.SUBMITTED: JobStatus.SUBMITTED,
        JobStatusEnum.RUNNING: JobStatus.RUNNING,
        JobStatusEnum.PAUSED: JobStatus.PAUSED,
        JobStatusEnum.PREEMPTED: JobStatus.PREEMPTED,
        JobStatusEnum.COMPLETED: JobStatus.COMPLETED,
        JobStatusEnum.FAILED: JobStatus.FAILED,
    }
    return status_map.get(status)


def _map_priority_enum(priority: JobPriorityEnum | None) -> JobPriority | None:
    """Map API priority enum to domain priority."""
    if priority is None:
        return None
    priority_map = {
        JobPriorityEnum.HIGH: JobPriority.HIGH,
        JobPriorityEnum.MEDIUM: JobPriority.MEDIUM,
        JobPriorityEnum.LOW: JobPriority.LOW,
    }
    return priority_map.get(priority)


def _job_to_summary(job) -> TrainingJobSummary:
    """Convert domain entity to summary response."""
    return TrainingJobSummary(
        id=job.id,
        job_name=job.job_name,
        display_name=job.display_name,
        owner_id=job.owner_id,
        owner_username=None,
        status=JobStatusEnum(job.status.value),
        priority=JobPriorityEnum(job.priority.value),
        instance_type=job.instance_type,
        node_count=job.node_count,
        current_epoch=job.current_epoch,
        latest_loss=job.latest_loss,
        checkpoints_count=0,
        submitted_at=job.submitted_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        duration_seconds=job.duration_seconds,
        estimated_cost_usd=job.estimated_cost_usd,
    )


def _job_to_detail(job) -> TrainingJobDetail:
    """Convert domain entity to detail response."""
    return TrainingJobDetail(
        id=job.id,
        job_name=job.job_name,
        display_name=job.display_name,
        description=job.description,
        owner_id=job.owner_id,
        owner_username=None,
        status=JobStatusEnum(job.status.value),
        hyperpod_status=job.hyperpod_status,
        kueue_workload_name=job.kueue_workload_name,
        kueue_status=job.kueue_status,
        image_uri=job.image_uri,
        instance_type=job.instance_type,
        node_count=job.node_count,
        tasks_per_node=job.tasks_per_node,
        entrypoint_command=job.entrypoint_command,
        environment_variables=job.environment_variables,
        dataset_id=job.dataset_id,
        dataset_name=None,
        data_mount_path=job.data_mount_path,
        checkpoint_mount_path=job.checkpoint_mount_path,
        hyperparameters=job.hyperparameters,
        max_epochs=job.max_epochs,
        batch_size=job.batch_size,
        learning_rate=job.learning_rate,
        distribution_strategy=job.distribution_strategy.value,
        priority=JobPriorityEnum(job.priority.value),
        mixed_precision=job.mixed_precision,
        use_spot_instances=job.use_spot_instances,
        total_pods=job.total_pods,
        running_pods=job.running_pods,
        failed_pods=job.failed_pods,
        preemption_count=job.preemption_count,
        current_epoch=job.current_epoch,
        current_step=job.current_step,
        latest_loss=job.latest_loss,
        latest_accuracy=job.latest_accuracy,
        submitted_at=job.submitted_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        duration_seconds=job.duration_seconds,
        total_gpu_hours=job.total_gpu_hours,
        estimated_cost_usd=job.estimated_cost_usd,
        error_message=job.error_message,
        failure_reason=job.failure_reason,
        hyperpod_job_arn=None,
        checkpoints_count=0,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


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
    job_data = {
        "job_name": data.job_name,
        "display_name": data.display_name,
        "description": data.description,
        "image_uri": data.image_uri,
        "instance_type": data.instance_type,
        "node_count": data.node_count,
        "tasks_per_node": data.tasks_per_node,
        "entrypoint_command": data.entrypoint_command,
        "environment_variables": data.environment_variables,
        "dataset_id": data.dataset_id,
        "data_mount_path": data.data_mount_path,
        "checkpoint_mount_path": data.checkpoint_mount_path,
        "checkpoint_interval": data.checkpoint_interval,
        "hyperparameters": data.hyperparameters,
        "max_epochs": data.max_epochs,
        "batch_size": data.batch_size,
        "learning_rate": data.learning_rate,
        "distribution_strategy": (
            data.distribution_strategy.value if data.distribution_strategy else "ddp"
        ),
        "priority": data.priority.value if data.priority else "medium",
        "mixed_precision": data.mixed_precision,
        "use_spot_instances": data.use_spot_instances,
    }

    job = await service.create_job(owner_id=current_user.user_id, data=job_data)
    return _job_to_detail(job)


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
    # Non-admin users only see their own jobs
    owner_id = None
    if current_user.role not in ["admin", "manager"]:
        owner_id = current_user.user_id

    jobs, total = await service.list_jobs(
        owner_id=owner_id,
        status=_map_status_enum(status),
        priority=_map_priority_enum(priority),
        submitted_after=submitted_after,
        submitted_before=submitted_before,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return TrainingJobListResponse(
        items=[_job_to_summary(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
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

    # Check ownership for non-admin users
    if current_user.role not in ["admin", "manager"]:
        if job.owner_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this job",
            )

    return _job_to_detail(job)


async def _check_job_permission(
    job_id: int,
    current_user: CurrentUser,
    service: TrainingJobService,
    action: str,
):
    """Check job exists and user has permission."""
    job = await service.get_job(job_id)
    if current_user.role not in ["admin", "manager"]:
        if job.owner_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have permission to {action} this job",
            )
    return job


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
    await _check_job_permission(job_id, current_user, service, "pause")
    job = await service.pause_job(job_id)
    return _job_to_detail(job)


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
    await _check_job_permission(job_id, current_user, service, "resume")
    job = await service.resume_job(job_id)
    return _job_to_detail(job)


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
    await _check_job_permission(job_id, current_user, service, "cancel")
    job = await service.cancel_job(job_id)
    return _job_to_detail(job)


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
    # First check if job exists and user has permission
    job = await service.get_job(job_id)
    if current_user.role not in ["admin", "manager"]:
        if job.owner_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this job",
            )

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
    # Check job exists and is running
    job = await service.get_job(job_id)

    # Check ownership
    if current_user.role not in ["admin", "manager"]:
        if job.owner_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create checkpoints for this job",
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
