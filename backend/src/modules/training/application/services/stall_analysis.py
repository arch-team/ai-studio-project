"""停滞分析逻辑.

负责分析训练指标数据，判断是否发生停滞。
"""

from datetime import datetime

import structlog

from src.modules.training.application.interfaces import IMetricsService, MetricPoint
from src.modules.training.application.services.stall_detection_config import (
    DEFAULT_METRIC_FALLBACK,
    StallCheckResult,
    StallDetectionConfig,
)
from src.modules.training.domain.entities import TrainingJob

logger = structlog.get_logger(__name__)


class StallAnalyzer:
    """停滞分析器"""

    def __init__(self, metrics_service: IMetricsService):
        self._metrics = metrics_service

    def get_metrics_to_try(self, config: StallDetectionConfig) -> list[str]:
        """获取需要尝试的指标列表（按优先级排序）

        Args:
            config: 停滞检测配置

        Returns:
            list[str]: 指标名称列表
        """
        if config.primary_metric == "loss":
            return DEFAULT_METRIC_FALLBACK

        # 主指标在前，其余按默认顺序
        return [config.primary_metric] + [m for m in DEFAULT_METRIC_FALLBACK if m != config.primary_metric]

    async def fetch_metric_points(
        self,
        job: TrainingJob,
        config: StallDetectionConfig,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[list[MetricPoint], str | None]:
        """获取指标数据点

        Args:
            job: 训练任务
            config: 配置
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            tuple: (指标点列表, 使用的指标名称)
        """
        metrics_to_try = self.get_metrics_to_try(config)

        assert job.id is not None, "Job must have ID to fetch metrics"
        for metric_name in metrics_to_try:
            points = await self._metrics.get_metric_history(
                job_id=job.id,
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
            )
            if points:
                logger.debug(
                    "metric_points_fetched",
                    job_id=job.id,
                    metric_name=metric_name,
                    point_count=len(points),
                )
                return points, metric_name

        logger.warning(
            "no_metrics_available",
            job_id=job.id,
            tried_metrics=metrics_to_try,
        )
        return [], None

    def analyze_stall(
        self,
        job_id: int,
        metric_points: list[MetricPoint],
        used_metric: str | None,
        config: StallDetectionConfig,
    ) -> StallCheckResult:
        """分析指标是否表明停滞

        Args:
            job_id: 任务 ID
            metric_points: 指标数据点
            used_metric: 使用的指标名称
            config: 配置

        Returns:
            StallCheckResult: 分析结果
        """
        # 提取值列表
        values = [p.value for p in metric_points]

        # 计算变化率
        change_rate = self.calculate_change_rate(values)

        # 判定是否停滞
        is_stalled = change_rate < config.change_rate_threshold

        if is_stalled:
            logger.warning(
                "stall_detected",
                job_id=job_id,
                metric_name=used_metric,
                change_rate=change_rate,
                threshold=config.change_rate_threshold,
            )

        return StallCheckResult(
            job_id=job_id,
            is_stalled=is_stalled,
            metric_name=used_metric,
            metric_values=values,
            change_rate=change_rate,
            detection_window_minutes=config.detection_window_minutes,
        )

    @staticmethod
    def calculate_change_rate(values: list[float]) -> float:
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