"""CloudWatch Logs 训练日志客户端。

使用 aioboto3 异步调用 CloudWatch Logs filter_log_events API，
获取 SageMaker HyperPod 训练任务的日志输出。

开发环境（无 AWS 凭证）gracefully 降级，返回提示信息。
"""

from datetime import UTC, datetime

import aioboto3
import structlog
from botocore.exceptions import ClientError

from src.modules.training.application.interfaces import LogEntryData

logger = structlog.get_logger(__name__)


class CloudWatchLogClient:
    """CloudWatch Logs 训练日志客户端。"""

    def __init__(
        self,
        region: str = "us-east-1",
        log_group_prefix: str = "/aws/sagemaker/TrainingJobs",
    ) -> None:
        self._region = region
        self._log_group_prefix = log_group_prefix
        self._session = aioboto3.Session()

    async def get_training_logs(
        self,
        job_name: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
        filter_pattern: str | None = None,
        next_token: str | None = None,
    ) -> tuple[list[LogEntryData], str | None]:
        """从 CloudWatch Logs 获取训练日志。

        Returns:
            (日志条目列表, 分页 token)
        """
        log_group_name = f"{self._log_group_prefix}/{job_name}"

        params: dict = {
            "logGroupName": log_group_name,
            "limit": min(limit, 10000),
            "interleaved": True,
        }

        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if filter_pattern:
            params["filterPattern"] = filter_pattern
        if next_token:
            params["nextToken"] = next_token

        try:
            async with self._session.client("logs", region_name=self._region) as logs_client:
                response = await logs_client.filter_log_events(**params)

            entries: list[LogEntryData] = []
            for event in response.get("events", []):
                timestamp = datetime.fromtimestamp(event["timestamp"] / 1000, tz=UTC)
                # 从 logStreamName 提取 pod 名称（格式: job-name/pod-name）
                log_stream = event.get("logStreamName", "")
                pod_name = log_stream.split("/")[-1] if "/" in log_stream else log_stream or None
                entries.append(
                    LogEntryData(
                        timestamp=timestamp,
                        pod_name=pod_name,
                        message=event.get("message", "").rstrip("\n"),
                    )
                )

            result_next_token = response.get("nextToken")
            logger.debug(
                "cloudwatch_logs_fetched",
                job_name=job_name,
                log_group=log_group_name,
                count=len(entries),
            )
            return entries, result_next_token

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                logger.info(
                    "cloudwatch_log_group_not_found",
                    job_name=job_name,
                    log_group=log_group_name,
                )
                return [], None

            logger.warning(
                "cloudwatch_logs_error",
                job_name=job_name,
                error_code=error_code,
                error=str(e),
            )
            return self._fallback_response(job_name, "CloudWatch Logs 查询失败"), None

        except Exception as e:
            # 开发环境无 AWS 凭证等情况，gracefully 降级
            logger.info(
                "cloudwatch_logs_unavailable",
                job_name=job_name,
                error=str(e),
            )
            return self._fallback_response(job_name, "CloudWatch Logs 不可用（开发环境）"), None

    def _fallback_response(self, job_name: str, reason: str) -> list[LogEntryData]:
        """生成降级提示日志。"""
        return [
            LogEntryData(
                timestamp=datetime.now(tz=UTC),
                pod_name=None,
                message=f"[{reason}] 训练任务 {job_name} 的日志暂不可用",
            )
        ]
