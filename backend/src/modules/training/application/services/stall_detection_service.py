"""训练任务停滞检测服务 (T037c)

职责:
- 监控训练指标变化率
- 检测停滞任务
- 发送告警通知

参考: spec.md FR-022 训练任务停滞检测机制
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from src.modules.training.application.interfaces import (
    Alert,
    IMetricsService,
    INotificationService,
    MetricPoint,
)
from src.modules.training.domain.entities.training_job import TrainingJob
from src.modules.training.domain.repositories.training_job_repository import (
    ITrainingJobRepository,
)
from src.modules.training.domain.value_objects import JobStatus
from src.shared.utils import utc_now

logger = logging.getLogger(__name__)

# 默认指标回退顺序
DEFAULT_METRIC_FALLBACK = ["loss", "accuracy", "perplexity"]


@dataclass
class StallDetectionConfig:
    """停滞检测配置"""

    primary_metric: str = "loss"
    detection_window_minutes: int = 30
    change_rate_threshold: float = 0.001  # 0.1%
    enabled: bool = True


@dataclass
class StallCheckResult:
    """停滞检查结果"""

    job_id: int
    is_stalled: bool
    metric_name: str | None = None
    metric_values: list[float] = field(default_factory=list)
    change_rate: float | None = None
    detection_window_minutes: int = 30
    skipped: bool = False
    skip_reason: str | None = None


# Re-export MetricPoint for tests
__all__ = [
    "StallDetectionService",
    "StallDetectionConfig",
    "StallCheckResult",
    "MetricPoint",
]


class StallDetectionService:
    """训练任务停滞检测服务 (T037c)

    职责:
    - 监控训练指标变化率
    - 检测停滞任务
    - 发送告警通知
    """

    def __init__(
        self,
        training_job_repository: ITrainingJobRepository,
        metrics_service: IMetricsService,
        notification_service: INotificationService | None = None,
    ) -> None:
        """初始化停滞检测服务

        Args:
            training_job_repository: 训练任务仓库接口
            metrics_service: 指标服务接口
            notification_service: 通知服务接口（可选）
        """
        self._repo = training_job_repository
        self._metrics = metrics_service
        self._notification = notification_service

    async def check_all_running_jobs(
        self,
        config: StallDetectionConfig | None = None,
    ) -> list[StallCheckResult]:
        """检查所有 Running 状态任务

        Args:
            config: 停滞检测配置

        Returns:
            list[StallCheckResult]: 检查结果列表
        """
        results: list[StallCheckResult] = []
        config = config or StallDetectionConfig()

        # 获取所有 Running 状态任务
        jobs, _ = await self._repo.list_jobs(status=JobStatus.RUNNING, page_size=1000)

        for job in jobs:
            try:
                result = await self.check_job_stall(job, config)
                results.append(result)
            except Exception as e:
                logger.error(f"检查任务 {job.job_name} 停滞状态失败: {e}")
                results.append(
                    StallCheckResult(
                        job_id=job.id,
                        is_stalled=False,
                        skipped=True,
                        skip_reason=f"error: {str(e)}",
                    )
                )

        return results

    async def check_job_stall(
        self,
        job: TrainingJob,
        config: StallDetectionConfig | None = None,
    ) -> StallCheckResult:
        """检查单个任务是否停滞

        Args:
            job: 训练任务实体
            config: 停滞检测配置

        Returns:
            StallCheckResult: 检查结果
        """
        config = config or StallDetectionConfig()

        # 检测禁用时跳过
        if not config.enabled:
            return StallCheckResult(
                job_id=job.id,
                is_stalled=False,
                skipped=True,
                skip_reason="disabled",
            )

        # 计算时间窗口
        end_time = utc_now()
        start_time = end_time - timedelta(minutes=config.detection_window_minutes)

        # 尝试获取指标数据（按回退顺序）
        metrics_to_try = (
            [config.primary_metric]
            if config.primary_metric != "loss"
            else DEFAULT_METRIC_FALLBACK
        )
        if config.primary_metric == "loss":
            metrics_to_try = DEFAULT_METRIC_FALLBACK
        else:
            metrics_to_try = [config.primary_metric] + [
                m for m in DEFAULT_METRIC_FALLBACK if m != config.primary_metric
            ]

        metric_points: list[MetricPoint] = []
        used_metric: str | None = None

        for metric_name in metrics_to_try:
            points = await self._metrics.get_metric_history(
                job_id=job.id,
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
            )
            if points:
                metric_points = points
                used_metric = metric_name
                break

        # 没有可用指标
        if not metric_points:
            return StallCheckResult(
                job_id=job.id,
                is_stalled=False,
                skipped=True,
                skip_reason="no_metrics",
                detection_window_minutes=config.detection_window_minutes,
            )

        # 提取值列表
        values = [p.value for p in metric_points]

        # 计算变化率
        change_rate = self._calculate_change_rate(values)

        # 判定是否停滞
        is_stalled = change_rate < config.change_rate_threshold

        return StallCheckResult(
            job_id=job.id,
            is_stalled=is_stalled,
            metric_name=used_metric,
            metric_values=values,
            change_rate=change_rate,
            detection_window_minutes=config.detection_window_minutes,
        )

    async def send_stall_alert(
        self,
        job: TrainingJob,
        result: StallCheckResult,
    ) -> None:
        """发送停滞告警

        Args:
            job: 训练任务实体
            result: 停滞检查结果
        """
        if not self._notification:
            logger.warning("通知服务未配置，跳过告警发送")
            return

        alert = Alert(
            title=f"训练任务停滞告警: {job.job_name}",
            message=(
                f"训练任务 {job.job_name} 检测到停滞。\n"
                f"监控指标: {result.metric_name}\n"
                f"变化率: {result.change_rate:.4%}\n"
                f"检测窗口: {result.detection_window_minutes} 分钟"
            ),
            severity="warning",
            recipient_ids=[job.owner_id],  # 发送给任务所有者
            metadata={
                "job_id": job.id,
                "job_name": job.job_name,
                "metric_name": result.metric_name,
                "change_rate": result.change_rate,
                "detection_window_minutes": result.detection_window_minutes,
            },
        )

        await self._notification.send_alert(alert)
        logger.info(f"已发送任务 {job.job_name} 停滞告警")

    @staticmethod
    def _calculate_change_rate(values: list[float]) -> float:
        """计算指标变化率

        Args:
            values: 指标值列表

        Returns:
            float: 变化率（绝对值）
        """
        if len(values) < 2:
            return 1.0  # 数据不足，返回高变化率（不判定为停滞）

        first_value = values[0]
        last_value = values[-1]

        if first_value == 0:
            return abs(last_value) if last_value != 0 else 0.0

        return abs((last_value - first_value) / first_value)
