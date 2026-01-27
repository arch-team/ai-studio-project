"""Shared Infrastructure External - AWS 外部服务客户端."""

from .cloudwatch_client import CloudWatchLogsClient, ICloudWatchLogsClient, get_cloudwatch_logs_client

__all__ = [
    "ICloudWatchLogsClient",
    "CloudWatchLogsClient",
    "get_cloudwatch_logs_client",
]
