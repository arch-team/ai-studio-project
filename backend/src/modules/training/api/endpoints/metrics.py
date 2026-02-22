"""Metrics, Logs and Debug Endpoints - 指标、日志和调试。"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.modules.auth.api.current_user import CurrentUser
from src.modules.auth.api.dependencies import get_current_active_user
from src.modules.auth.api.permissions import check_resource_owner_or_privileged
from src.modules.training.api.dependencies import (
    get_kueue_client,
    get_training_job_service,
    get_training_log_client,
    get_training_metrics_service,
)
from src.modules.training.api.schemas import (
    JobMetricsComparisonResponse,
    JobMetricsData,
    KueueDebugResponse,
    KueueWorkloadStatus,
    LogEntry,
    MetricDataPoint,
    PreemptionEvent,
    QueueInfo,
    TrainingLogsResponse,
    TrainingMetricsResponse,
)
from src.modules.training.application.interfaces.kueue_client import IKueueClient
from src.modules.training.application.interfaces.log_client import ITrainingLogClient
from src.modules.training.application.services import (
    TrainingJobService,
    TrainingMetricsService,
)
from src.modules.training.domain.value_objects import JobStatus

router = APIRouter()

# 默认指标类型
DEFAULT_METRIC_NAMES = ["loss", "accuracy", "learning_rate", "throughput"]


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
    log_client: ITrainingLogClient = Depends(get_training_log_client),
) -> TrainingLogsResponse:
    """Get training job logs.

    Retrieves logs from CloudWatch Logs (stdout/stderr).
    Supports filtering by time range, pattern, and specific pod.
    开发环境无 CloudWatch 时 gracefully 降级返回提示信息。
    """
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "view logs of")

    # 转换时间为毫秒时间戳（CloudWatch API 使用毫秒）
    start_ms = int(start_time.timestamp() * 1000) if start_time else None
    end_ms = int(end_time.timestamp() * 1000) if end_time else None

    entries, next_token = await log_client.get_training_logs(
        job_name=job.job_name,
        start_time=start_ms,
        end_time=end_ms,
        limit=tail,
        filter_pattern=filter_pattern,
    )

    # 如果指定了 pod_name，在应用层过滤
    logs = [
        LogEntry(timestamp=e.timestamp, pod_name=e.pod_name, message=e.message)
        for e in entries
        if pod_name is None or e.pod_name == pod_name
    ]

    return TrainingLogsResponse(logs=logs, next_token=next_token)


@router.get("/{job_id}/debug/kueue")
async def get_kueue_debug_info(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: TrainingJobService = Depends(get_training_job_service),
    kueue_client: IKueueClient = Depends(get_kueue_client),
) -> KueueDebugResponse:
    """Get Kueue Workload debug information.

    从 Kueue API 获取真实调度状态用于排障。
    开发环境无 K8s 集群时根据任务状态推断返回 fallback 数据。
    """
    job = await service.get_job(job_id)
    check_resource_owner_or_privileged(job.owner_id, current_user, "training job", "view debug info of")

    workload_name = job.kueue_workload_name or f"job-{job_id}-workload"

    # 尝试从 Kueue API 获取真实状态
    workload_data = await kueue_client.get_workload_status(
        workload_name=workload_name,
        namespace="training-jobs",
    )

    if workload_data is not None:
        # 真实 Kueue API 数据
        preemption_history = None
        if workload_data.preemption_history:
            preemption_history = [
                PreemptionEvent(
                    preempted_at=ev["preempted_at"],
                    preempting_workload=ev.get("preempting_workload"),
                    reason=ev.get("reason"),
                )
                for ev in workload_data.preemption_history
            ]

        response = KueueDebugResponse(
            workload_name=workload_data.workload_name,
            namespace=workload_data.namespace,
            status=KueueWorkloadStatus(
                admitted=workload_data.admitted,
                quota_reserved=workload_data.quota_reserved,
                pods_ready=workload_data.pods_ready,
                evicted=workload_data.evicted,
                finished=workload_data.finished,
            ),
            queue_info=QueueInfo(
                local_queue=workload_data.local_queue,
                cluster_queue=workload_data.cluster_queue,
                queue_position=workload_data.queue_position,
            ),
            preemption_history=preemption_history,
            raw_yaml=None,
        )
    else:
        # Fallback: 根据任务状态推断（开发环境或 Kueue 不可用）
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
            raw_yaml=None,
        )

    # 仅管理员可见 raw YAML
    if current_user.is_admin and workload_data and workload_data.raw_yaml:
        response.raw_yaml = workload_data.raw_yaml

    return response
