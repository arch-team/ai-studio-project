"""训练指标查询服务 (T220).

提供训练任务指标查询和对比功能，集成 Prometheus 指标采集。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.monitoring.application.services import PrometheusService


@dataclass
class MetricPoint:
    """单个指标数据点."""

    timestamp: datetime
    value: float


@dataclass
class TrainingMetricsResult:
    """训练指标查询结果."""

    job_id: int
    metrics: dict[str, list[MetricPoint]] = field(default_factory=dict)


@dataclass
class JobMetricsData:
    """单个任务的指标数据."""

    job_id: int
    metric_type: str
    data_points: list[MetricPoint] = field(default_factory=list)


@dataclass
class JobMetricsComparison:
    """多任务指标对比结果."""

    metric_type: str
    jobs: list[JobMetricsData] = field(default_factory=list)


# 指标名称映射
METRIC_TYPE_MAPPING = {
    "loss": "training_loss",
    "accuracy": "training_accuracy",
    "learning_rate": "training_learning_rate",
    "throughput": "training_throughput",
    "gpu_memory": "training_gpu_memory",
}


class TrainingMetricsService:
    """训练指标查询服务.

    提供训练任务指标的查询、聚合和对比功能。
    """

    def __init__(self, prometheus_service: "PrometheusService") -> None:
        """初始化服务.

        Args:
            prometheus_service: Prometheus 指标服务
        """
        self._prometheus = prometheus_service
        self._cache: dict[str, TrainingMetricsResult] = {}

    async def get_training_metrics(
        self,
        job_id: int,
        metric_types: list[str],
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        step: str | None = None,
        is_completed: bool = False,
    ) -> TrainingMetricsResult:
        """获取训练任务指标.

        Args:
            job_id: 任务 ID
            metric_types: 指标类型列表 (loss, accuracy, learning_rate 等)
            start_time: 查询开始时间
            end_time: 查询结束时间
            step: 聚合步长 (如 "5m", "1h")
            is_completed: 任务是否已完成 (用于缓存策略)

        Returns:
            训练指标查询结果
        """
        # 缓存键
        cache_key = f"{job_id}:{','.join(sorted(metric_types))}"

        # 对于已完成任务，尝试使用缓存
        if is_completed and cache_key in self._cache:
            return self._cache[cache_key]

        # 转换指标类型为 Prometheus 指标名称
        prometheus_metric_names = [
            METRIC_TYPE_MAPPING.get(mt, f"training_{mt}") for mt in metric_types
        ]

        # 查询 Prometheus
        raw_metrics = await self._prometheus.query_metrics(
            metric_names=prometheus_metric_names,
            start_time=start_time,
            end_time=end_time,
            step=step,
        )

        # 转换结果
        result_metrics: dict[str, list[MetricPoint]] = {}

        for metric_type in metric_types:
            prometheus_name = METRIC_TYPE_MAPPING.get(
                metric_type, f"training_{metric_type}"
            )
            if prometheus_name in raw_metrics:
                result_metrics[metric_type] = [
                    MetricPoint(timestamp=dp.timestamp, value=dp.value)
                    for dp in raw_metrics[prometheus_name]
                ]

        result = TrainingMetricsResult(job_id=job_id, metrics=result_metrics)

        # 缓存已完成任务的结果
        if is_completed:
            self._cache[cache_key] = result

        return result

    async def compare_jobs_metrics(
        self,
        job_ids: list[int],
        metric_type: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> JobMetricsComparison:
        """对比多个任务的指标.

        Args:
            job_ids: 任务 ID 列表
            metric_type: 指标类型
            start_time: 查询开始时间
            end_time: 查询结束时间

        Returns:
            多任务指标对比结果
        """
        jobs_data: list[JobMetricsData] = []

        # 为每个任务获取指标
        for job_id in job_ids:
            result = await self.get_training_metrics(
                job_id=job_id,
                metric_types=[metric_type],
                start_time=start_time,
                end_time=end_time,
            )

            data_points = result.metrics.get(metric_type, [])
            jobs_data.append(
                JobMetricsData(
                    job_id=job_id,
                    metric_type=metric_type,
                    data_points=data_points,
                )
            )

        return JobMetricsComparison(metric_type=metric_type, jobs=jobs_data)

    def clear_cache(self, job_id: int | None = None) -> None:
        """清除缓存.

        Args:
            job_id: 指定任务 ID 清除，None 表示清除全部
        """
        if job_id is None:
            self._cache.clear()
        else:
            keys_to_remove = [k for k in self._cache if k.startswith(f"{job_id}:")]
            for key in keys_to_remove:
                del self._cache[key]
