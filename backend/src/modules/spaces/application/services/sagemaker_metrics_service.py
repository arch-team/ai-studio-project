"""SageMaker Spaces 启动性能监控服务 (T085b)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import aioboto3
import structlog

from src.shared.infrastructure import get_settings

logger = structlog.get_logger(__name__)


class SpaceMetricsService:
    """SageMaker Spaces 启动性能监控.

    集成 CloudWatch Metrics 监控 Space 启动时间，提供 P50/P95/P99 统计和超时告警。
    """

    NAMESPACE = "AITrainingPlatform/Spaces"
    STARTUP_TIMEOUT_SECONDS = 180  # 3 分钟

    def __init__(self) -> None:
        settings = get_settings()
        self._region = settings.aws_region
        self._session = aioboto3.Session()

    async def record_startup_time(self, space_id: str, startup_seconds: float) -> None:
        """记录 Space 启动耗时到 CloudWatch.

        Args:
            space_id: 平台 Space ID
            startup_seconds: 从 CreateSpace API 调用到 InService 状态的耗时 (秒)
        """
        try:
            async with self._session.client("cloudwatch", region_name=self._region) as cw:
                await cw.put_metric_data(
                    Namespace=self.NAMESPACE,
                    MetricData=[
                        {
                            "MetricName": "SpaceStartupTime",
                            "Value": startup_seconds,
                            "Unit": "Seconds",
                            "Dimensions": [
                                {"Name": "SpaceId", "Value": space_id},
                            ],
                            "Timestamp": datetime.now(UTC),
                        }
                    ],
                )

            logger.info(
                "space_startup_time_recorded",
                space_id=space_id,
                startup_seconds=startup_seconds,
            )

            # 检查是否超时并记录告警
            if startup_seconds > self.STARTUP_TIMEOUT_SECONDS:
                logger.warning(
                    "space_startup_timeout",
                    space_id=space_id,
                    startup_seconds=startup_seconds,
                    timeout_threshold=self.STARTUP_TIMEOUT_SECONDS,
                )

        except Exception as e:
            logger.error(
                "space_startup_time_record_failed",
                space_id=space_id,
                error=str(e),
            )

    async def get_startup_statistics(self, period_hours: int = 24) -> dict[str, Any]:
        """获取启动时间统计 (P50/P95/P99).

        Args:
            period_hours: 统计时间范围 (小时)

        Returns:
            包含 P50/P95/P99 和平均值的统计字典
        """
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=period_hours)

        try:
            async with self._session.client("cloudwatch", region_name=self._region) as cw:
                response: dict[str, Any] = await cw.get_metric_statistics(
                    Namespace=self.NAMESPACE,
                    MetricName="SpaceStartupTime",
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=period_hours * 3600,  # 整个时间段作为一个 Period
                    Statistics=["Average", "Minimum", "Maximum", "SampleCount"],
                    ExtendedStatistics=["p50", "p95", "p99"],
                    Unit="Seconds",
                )

            datapoints = response.get("Datapoints", [])
            if not datapoints:
                logger.info("space_startup_no_data", period_hours=period_hours)
                return {
                    "period_hours": period_hours,
                    "sample_count": 0,
                    "average": 0.0,
                    "minimum": 0.0,
                    "maximum": 0.0,
                    "p50": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                }

            # 取最新的数据点
            latest = datapoints[0]
            extended = latest.get("ExtendedStatistics", {})

            stats = {
                "period_hours": period_hours,
                "sample_count": int(latest.get("SampleCount", 0)),
                "average": latest.get("Average", 0.0),
                "minimum": latest.get("Minimum", 0.0),
                "maximum": latest.get("Maximum", 0.0),
                "p50": extended.get("p50", 0.0),
                "p95": extended.get("p95", 0.0),
                "p99": extended.get("p99", 0.0),
            }

            logger.info("space_startup_statistics", **stats)
            return stats

        except Exception as e:
            logger.error("space_startup_statistics_failed", error=str(e))
            return {
                "period_hours": period_hours,
                "sample_count": 0,
                "average": 0.0,
                "minimum": 0.0,
                "maximum": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "error": str(e),
            }

    async def check_startup_timeout(self, space_id: str, created_at: datetime) -> bool:
        """检查 Space 是否启动超时 (>3 分钟).

        Args:
            space_id: 平台 Space ID
            created_at: Space 创建时间

        Returns:
            True 表示已超时
        """
        now = datetime.now(UTC)

        # 确保 created_at 有时区信息
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        elapsed_seconds = (now - created_at).total_seconds()
        is_timeout = elapsed_seconds > self.STARTUP_TIMEOUT_SECONDS

        if is_timeout:
            logger.warning(
                "space_startup_timeout_detected",
                space_id=space_id,
                elapsed_seconds=elapsed_seconds,
                timeout_threshold=self.STARTUP_TIMEOUT_SECONDS,
            )

        return is_timeout
