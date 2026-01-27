"""AWS CloudWatch Logs 客户端实现 (T073)."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from functools import lru_cache
from typing import Any

import aioboto3

from src.shared.infrastructure import get_settings


class ICloudWatchLogsClient(ABC):
    """CloudWatch Logs 客户端接口."""

    @abstractmethod
    async def query_logs(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """执行 CloudWatch Logs Insights 查询."""
        pass

    @abstractmethod
    async def query_training_job_logs(
        self,
        job_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """查询指定训练任务的日志."""
        pass

    @abstractmethod
    async def search_logs(
        self,
        keyword: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """搜索包含关键字的日志."""
        pass


class CloudWatchLogsClient(ICloudWatchLogsClient):
    """AWS CloudWatch Logs 客户端异步实现.

    使用 aioboto3 进行异步 AWS CloudWatch Logs API 调用，支持 Logs Insights 查询。
    实现单例模式 (通过 lru_cache)。
    """

    LOG_GROUP_NAME = "/aws/hyperpod/training-platform"
    RETENTION_DAYS = 30

    def __init__(self) -> None:
        settings = get_settings()
        self._region = getattr(settings, "aws_region", "us-east-1")
        self._session = aioboto3.Session()

    async def _get_logs_client(self) -> Any:
        """获取 CloudWatch Logs 客户端上下文管理器.

        Returns:
            CloudWatch Logs 客户端异步上下文管理器
        """
        return self._session.client("logs", region_name=self._region)

    async def _start_query(
        self,
        query_string: str,
        start_time: datetime,
        end_time: datetime,
        limit: int,
    ) -> str:
        """启动 CloudWatch Logs Insights 查询.

        Args:
            query_string: Logs Insights 查询语句
            start_time: 查询开始时间
            end_time: 查询结束时间
            limit: 结果数量限制

        Returns:
            查询 ID
        """
        async with await self._get_logs_client() as logs:
            response: dict[str, Any] = await logs.start_query(
                logGroupName=self.LOG_GROUP_NAME,
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=query_string,
                limit=limit,
            )
            query_id: str = response["queryId"]
            return query_id

    async def _get_query_results(
        self,
        query_id: str,
        max_retries: int = 30,
        retry_interval: float = 1.0,
    ) -> list[dict[str, Any]]:
        """获取查询结果 (轮询直到完成).

        Args:
            query_id: 查询 ID
            max_retries: 最大重试次数
            retry_interval: 重试间隔 (秒)

        Returns:
            查询结果列表

        Raises:
            TimeoutError: 查询超时
        """
        async with await self._get_logs_client() as logs:
            for _ in range(max_retries):
                response: dict[str, Any] = await logs.get_query_results(queryId=query_id)
                status = response["status"]

                if status == "Complete":
                    return self._parse_results(response.get("results", []))
                elif status in ("Failed", "Cancelled", "Timeout"):
                    raise RuntimeError(f"查询失败: {status}")

                await asyncio.sleep(retry_interval)

            raise TimeoutError(f"查询超时: 超过 {max_retries} 次重试")

    def _parse_results(self, raw_results: list[list[dict[str, str]]]) -> list[dict[str, Any]]:
        """解析 Logs Insights 查询结果.

        Args:
            raw_results: 原始查询结果 (嵌套列表结构)

        Returns:
            解析后的结果字典列表

        Example:
            Input: [[{'field': 'timestamp', 'value': '2024-01-27 10:00:00'}, ...]]
            Output: [{'timestamp': '2024-01-27 10:00:00', ...}]
        """
        parsed_results = []
        for result in raw_results:
            parsed_result = {}
            for field in result:
                field_name = field.get("field", "")
                field_value = field.get("value", "")
                if field_name and field_name != "@ptr":  # @ptr 是内部指针字段
                    parsed_result[field_name] = field_value
            parsed_results.append(parsed_result)
        return parsed_results

    async def query_logs(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """执行 CloudWatch Logs Insights 查询."""
        query_id = await self._start_query(query, start_time, end_time, limit)
        return await self._get_query_results(query_id)

    async def query_training_job_logs(
        self,
        job_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """查询指定训练任务的日志.

        Args:
            job_id: 训练任务 ID
            start_time: 查询开始时间
            end_time: 查询结束时间
            limit: 结果数量限制

        Returns:
            日志记录列表 (包含 @timestamp, @message 等字段)
        """
        query = f"""
        fields @timestamp, @message
        | filter job_id = "{job_id}"
        | sort @timestamp desc
        | limit {limit}
        """
        return await self.query_logs(query.strip(), start_time, end_time, limit)

    async def search_logs(
        self,
        keyword: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """搜索包含关键字的日志.

        Args:
            keyword: 搜索关键字
            start_time: 查询开始时间
            end_time: 查询结束时间
            limit: 结果数量限制

        Returns:
            匹配的日志记录列表
        """
        query = f"""
        fields @timestamp, @message, job_id
        | filter @message like /{keyword}/
        | sort @timestamp desc
        | limit {limit}
        """
        return await self.query_logs(query.strip(), start_time, end_time, limit)


@lru_cache(maxsize=1)
def get_cloudwatch_logs_client() -> CloudWatchLogsClient:
    """获取 CloudWatch Logs 客户端单例.

    使用 lru_cache 实现单例模式，避免重复创建 AWS 客户端。

    Returns:
        CloudWatchLogsClient: 单例客户端实例
    """
    return CloudWatchLogsClient()
