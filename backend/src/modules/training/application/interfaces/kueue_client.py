"""Kueue 队列状态查询客户端接口。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class KueueWorkloadData:
    """Kueue Workload 状态数据。"""

    workload_name: str
    namespace: str
    admitted: bool
    quota_reserved: bool
    pods_ready: bool
    evicted: bool
    finished: bool
    local_queue: str | None = None
    cluster_queue: str | None = None
    queue_position: int | None = None
    conditions: list[dict[str, Any]] | None = None
    admission: dict[str, Any] | None = None
    raw_yaml: str | None = None
    preemption_history: list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class PreemptionEventData:
    """抢占历史事件数据。"""

    preempted_at: datetime
    preempting_workload: str | None = None
    reason: str | None = None


class IKueueClient(Protocol):
    """Kueue 队列状态查询客户端接口。"""

    async def get_workload_status(
        self,
        workload_name: str,
        namespace: str = "training-jobs",
    ) -> KueueWorkloadData | None:
        """获取指定 Workload 的 Kueue 状态。

        Returns:
            Workload 状态数据，不存在时返回 None
        """
        ...
