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
    get_job_template_service,
    get_training_job_service,
    get_training_metrics_service,
)
from src.modules.training.api.schemas import (
    CheckpointResponse,
    CheckpointStatusEnum,
    CheckpointTypeEnum,
    CreateCheckpointRequest,
    CreateJobFromTemplateRequest,
    CreateTrainingJobRequest,
    JobMetricsComparisonResponse,
    JobMetricsData,
    JobPriorityEnum,
    JobStatusEnum,
    KueueDebugResponse,
    MetricDataPoint,
    StorageTierEnum,
    TrainingJobDetail,
    TrainingJobListResponse,
    TrainingJobSummary,
    TrainingLogsResponse,
    TrainingMetricsResponse,
    UpdateTrainingJobRequest,
)
from src.modules.training.application.services import (
    CheckpointService,
    JobTemplateService,
    TrainingJobService,
    TrainingMetricsService,
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
from src.shared.utils import EnumMapper, utc_now

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


@router.get("/{job_id}", response_model=TrainingJobDetail)
async def get_training_job(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
) -> TrainingJobDetail:
    """Get training job details by ID."""
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "view")
    response = TrainingJobDetail.from_entity(job)
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


# === Checkpoint Endpoints ===


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


# === Create Job from Template ===


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


# === Logs Endpoint ===


@router.get("/{job_id}/logs")
async def get_training_job_logs(
    job_id: int,
    tail: int = Query(default=100, ge=1, le=10000, description="Number of log lines to return"),
    start_time: datetime | None = Query(default=None, description="Log start time"),
    end_time: datetime | None = Query(default=None, description="Log end time"),
    filter_pattern: str | None = Query(default=None, description="Filter pattern (e.g., 'ERROR')"),
    pod_name: str | None = Query(default=None, description="Filter by specific pod"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
) -> TrainingLogsResponse:
    """Get training job logs.

    Retrieves logs from the training containers (stdout/stderr).
    Supports filtering by time range, pattern, and specific pod.
    """
    from src.modules.training.api.schemas import LogEntry, TrainingLogsResponse

    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "view logs of")

    # TODO: Integrate with CloudWatch Logs or HyperPod log API
    # For now, return a placeholder response
    logs = [
        LogEntry(
            timestamp=utc_now(),
            pod_name=f"{job.job_name}-worker-0",
            message=f"Training job {job.job_name} is in {job.status.value} state",
        )
    ]

    return TrainingLogsResponse(logs=logs, next_token=None)


# === Kueue Debug Endpoint ===


@router.get("/{job_id}/debug/kueue")
async def get_kueue_debug_info(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
) -> KueueDebugResponse:
    """Get Kueue Workload debug information.

    Returns detailed Kueue scheduling status for troubleshooting.
    Only accessible by job owner or admin.
    """
    from src.modules.training.api.schemas import (
        KueueDebugResponse,
        KueueWorkloadStatus,
        QueueInfo,
    )

    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "view debug info of")

    # Build Kueue workload name
    workload_name = job.kueue_workload_name or f"job-{job_id}-workload"

    # TODO: Integrate with Kueue API to get real status
    # For now, return a placeholder based on job status
    is_admitted = job.status in (JobStatus.RUNNING, JobStatus.PAUSED)
    is_finished = job.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    response = KueueDebugResponse(
        workload_name=workload_name,
        namespace="training-jobs",
        status=KueueWorkloadStatus(
            admitted=is_admitted,
            quota_reserved=is_admitted,
            pods_ready=job.status == JobStatus.RUNNING,
            evicted=job.status == JobStatus.PREEMPTED,
            finished=is_finished,
        ),
        queue_info=QueueInfo(
            local_queue=f"user-{job.owner_id}-queue",
            cluster_queue="default-cluster-queue",
            queue_position=None if is_admitted else 1,
        ),
        preemption_history=None,
        raw_yaml=None,  # Only for admin
    )

    # Include raw YAML only for admin
    if current_user.is_admin:
        response.raw_yaml = f"# Workload YAML for {workload_name}\n# (placeholder)"

    return response


# === Training Metrics Endpoints (T220) ===

# 默认指标类型
DEFAULT_METRIC_NAMES = ["loss", "accuracy", "learning_rate", "throughput"]


@router.get("/{job_id}/metrics", response_model=TrainingMetricsResponse)
async def get_training_metrics(
    job_id: int,
    metric_names: list[str] | None = Query(
        default=None, description="指标名称列表 (默认: loss, accuracy, learning_rate, throughput)"
    ),
    start_time: datetime | None = Query(default=None, description="查询开始时间"),
    end_time: datetime | None = Query(default=None, description="查询结束时间"),
    step: str | None = Query(default=None, description="聚合步长 (如 5m, 1h)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    job_service: TrainingJobService = Depends(get_training_job_service),
    metrics_service: TrainingMetricsService = Depends(get_training_metrics_service),
) -> TrainingMetricsResponse:
    """获取训练任务指标 (FR-026).

    从 Prometheus 查询训练任务的各类指标数据。
    支持时间范围过滤和聚合步长配置。
    """
    # 验证任务存在且有权限
    job = await job_service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "view metrics of")

    # 使用默认指标名称
    effective_metric_names = metric_names or DEFAULT_METRIC_NAMES

    # 判断任务是否已完成 (用于缓存策略)
    is_completed = job.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    # 查询指标
    result = await metrics_service.get_training_metrics(
        job_id=job_id,
        metric_types=effective_metric_names,
        start_time=start_time,
        end_time=end_time,
        step=step,
        is_completed=is_completed,
    )

    # 转换为响应格式
    metrics_data: dict[str, list[MetricDataPoint]] = {}
    for metric_type, points in result.metrics.items():
        metrics_data[metric_type] = [MetricDataPoint(timestamp=p.timestamp, value=p.value) for p in points]

    return TrainingMetricsResponse(job_id=job_id, metrics=metrics_data)


@router.get("/compare-metrics", response_model=JobMetricsComparisonResponse)
async def compare_jobs_metrics(
    job_ids: list[int] = Query(..., description="要对比的任务 ID 列表"),
    metric_type: str = Query(..., description="指标类型 (如 loss, accuracy)"),
    start_time: datetime | None = Query(default=None, description="查询开始时间"),
    end_time: datetime | None = Query(default=None, description="查询结束时间"),
    current_user: CurrentUser = Depends(get_current_active_user),
    job_service: TrainingJobService = Depends(get_training_job_service),
    metrics_service: TrainingMetricsService = Depends(get_training_metrics_service),
) -> JobMetricsComparisonResponse:
    """对比多个训练任务的指标 (FR-026).

    支持同时对比多个任务的同一指标，用于分析训练效果。
    """
    # 验证所有任务都存在且有权限
    for jid in job_ids:
        job = await job_service.get_job(jid)
        check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "view metrics of")

    # 查询对比数据
    result = await metrics_service.compare_jobs_metrics(
        job_ids=job_ids,
        metric_type=metric_type,
        start_time=start_time,
        end_time=end_time,
    )

    # 转换为响应格式
    jobs_data: list[JobMetricsData] = []
    for job_data in result.jobs:
        data_points = [MetricDataPoint(timestamp=p.timestamp, value=p.value) for p in job_data.data_points]
        jobs_data.append(
            JobMetricsData(
                job_id=job_data.job_id,
                metric_type=job_data.metric_type,
                data_points=data_points,
            )
        )

    return JobMetricsComparisonResponse(metric_type=metric_type, jobs=jobs_data)
