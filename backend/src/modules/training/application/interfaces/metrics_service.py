"""训练指标查询服务接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class MetricPoint:
    """指标数据点"""

    timestamp: datetime
    value: float


@dataclass
class MetricData:
    """完整的指标数据"""

    name: str
    points: list[MetricPoint]
    unit: str | None = None
    metadata: dict[str, Any] | None = None


class IMetricsService(ABC):
    """指标服务接口

    提供训练指标的查询能力，支持按时间范围获取指标历史。
    实现可以对接 CloudWatch、Prometheus 或自定义指标存储。
    """

    @abstractmethod
    async def get_metric_history(
        self,
        job_id: int,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[MetricPoint]:
        """获取指定任务的指标历史数据

        Args:
            job_id: 训练任务 ID
            metric_name: 指标名称 (如 'loss', 'accuracy', 'perplexity')
            start_time: 查询起始时间
            end_time: 查询结束时间

        Returns:
            list[MetricPoint]: 指标数据点列表，按时间升序排列
        """

    @abstractmethod
    async def get_multiple_metrics(
        self,
        job_id: int,
        metric_names: list[str],
        start_time: datetime,
        end_time: datetime,
    ) -> list[MetricData]:
        """批量获取多个指标的历史数据

        Args:
            job_id: 训练任务 ID
            metric_names: 指标名称列表
            start_time: 查询起始时间
            end_time: 查询结束时间

        Returns:
            list[MetricData]: 指标数据列表
        """

    @abstractmethod
    async def get_latest_metrics(
        self,
        job_id: int,
        metric_names: list[str] | None = None,
    ) -> dict[str, float]:
        """获取最新的指标值

        Args:
            job_id: 训练任务 ID
            metric_names: 指标名称列表，None 表示获取所有指标

        Returns:
            dict[str, float]: 指标名称到最新值的映射
        """
