"""训练日志客户端接口。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class LogEntryData:
    """日志条目数据。"""

    timestamp: datetime
    pod_name: str | None
    message: str


class ITrainingLogClient(Protocol):
    """训练日志获取客户端接口。"""

    async def get_training_logs(
        self,
        job_name: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
        filter_pattern: str | None = None,
        next_token: str | None = None,
    ) -> tuple[list[LogEntryData], str | None]:
        """获取训练日志。

        Returns:
            (日志条目列表, 分页 token)
        """
        ...
