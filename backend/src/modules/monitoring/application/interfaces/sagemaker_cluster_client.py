"""SageMaker 集群客户端接口定义 (Application 层).

将接口放在 Application 层，遵循 Clean Architecture 依赖方向：
Infrastructure 层实现应依赖 Application 层定义的抽象，而非反向。
"""

from abc import ABC, abstractmethod
from typing import Any


class ISageMakerClusterClient(ABC):
    """SageMaker HyperPod 集群只读客户端接口."""

    @abstractmethod
    async def describe_cluster(self, cluster_name: str) -> dict[str, Any]:
        """获取集群详细信息（原生 SageMaker 响应）.

        Args:
            cluster_name: HyperPod 集群名称

        Returns:
            SageMaker describe-cluster 原生响应 dict

        Raises:
            botocore.exceptions.ClientError: SageMaker API 调用失败（集群不存在、权限不足等）
            botocore.exceptions.EndpointConnectionError: 无法连接到 SageMaker 端点
        """
