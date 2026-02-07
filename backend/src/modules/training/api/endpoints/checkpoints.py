"""Checkpoint Endpoints - 检查点管理。"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import require_engineer
from src.modules.auth.api.permissions import check_resource_owner_or_privileged
from src.modules.training.api.dependencies import (
    get_checkpoint_service,
    get_training_job_service,
)
from src.modules.training.api.schemas import (
    CheckpointResponse,
    CheckpointStatusEnum,
    CheckpointTypeEnum,
    CreateCheckpointRequest,
    StorageTierEnum,
)
from src.modules.training.application.services import (
    CheckpointService,
    TrainingJobService,
)
from src.modules.training.domain.value_objects import JobStatus
from src.shared.utils import utc_now

router = APIRouter()


@router.post("/{job_id}/checkpoints", response_model=CheckpointResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_checkpoint(
    job_id: int,
    data: CreateCheckpointRequest | None = None,
    current_user: CurrentUser = Depends(require_engineer),
    service: TrainingJobService = Depends(get_training_job_service),
    checkpoint_service: CheckpointService = Depends(get_checkpoint_service),
) -> CheckpointResponse:
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

    assert checkpoint.id is not None, "Checkpoint must have ID"
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
