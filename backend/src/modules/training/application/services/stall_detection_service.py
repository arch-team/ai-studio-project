"""训练任务停滞检测服务 (T037c)

协调停滞检测、分析和告警通知。

参考: spec.md FR-022 训练任务停滞检测机制
"""

from datetime import timedelta

import structlog

from src.modules.training.application.interfaces import (
    Alert,
    IMetricsService,
    INotificationService,
    MetricPoint,
)
from src.modules.training.application.services.stall_analysis import StallAnalyzer
from src.modules.training.application.services.stall_detection_config import (
    StallCheckResult,
    StallDetectionConfig,
)
from src.modules.training.domain.entities.training_job import TrainingJob
from src.modules.training.domain.repositories.training_job_repository import (
    ITrainingJobRepository,
)
from src.modules.training.domain.value_objects import JobStatus
from src.shared.utils import utc_now

logger = structlog.get_logger(__name__)


# Re-export for compatibility
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
        self._analyzer = StallAnalyzer(metrics_service)

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

                # 发送告警
                if result.is_stalled:
                    await self.send_stall_alert(job, result)

            except Exception as e:
                logger.exception(
                    "stall_check_failed",
                    job_id=job.id,
                    job_name=job.job_name,
                    error_type=type(e).__name__,
                    error=str(e),
                )
                results.append(
                    StallCheckResult(
                        job_id=job.id or 0,
                        is_stalled=False,
                        skipped=True,
                        skip_reason=f"error: {type(e).__name__}: {e}",
                    )
                )

        logger.info(
            "stall_check_completed",
            total_jobs=len(jobs),
            stalled_count=sum(1 for r in results if r.is_stalled),
            skipped_count=sum(1 for r in results if r.skipped),
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
        job_id = job.id or 0

        # 检测禁用时跳过
        if not config.enabled:
            return StallCheckResult(
                job_id=job_id,
                is_stalled=False,
                skipped=True,
                skip_reason="disabled",
            )

        # 计算时间窗口
        end_time = utc_now()
        start_time = end_time - timedelta(minutes=config.detection_window_minutes)

        # 获取指标数据
        metric_points, used_metric = await self._analyzer.fetch_metric_points(
            job, config, start_time, end_time
        )

        # 没有可用指标
        if not metric_points:
            return StallCheckResult(
                job_id=job_id,
                is_stalled=False,
                skipped=True,
                skip_reason="no_metrics",
                detection_window_minutes=config.detection_window_minutes,
            )

        # 分析停滞状态
        return self._analyzer.analyze_stall(
            job_id=job_id,
            metric_points=metric_points,
            used_metric=used_metric,
            config=config,
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
            logger.warning("notification_service_not_configured")
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
        logger.info("stall_alert_sent", job_name=job.job_name)