"""SageMaker 集群只读客户端 (Task 2C.2b).

为监控页"集群概览"提供 describe-cluster 回源能力。
读穿透缓存策略下，此客户端仅在 DB 记录缺失/过期时被调用。
使用 aioboto3 原生异步，禁止 boto3 + run_in_executor。
"""

from functools import lru_cache
from typing import Any

import aioboto3
import structlog

from src.shared.infrastructure import get_settings

from ...application.interfaces.sagemaker_cluster_client import ISageMakerClusterClient

logger = structlog.get_logger(__name__)


class SageMakerClusterClient(ISageMakerClusterClient):
    """SageMaker HyperPod 集群只读客户端.

    薄封装 aioboto3 describe_cluster，暴露原生响应 dict。
    """

    def __init__(self, session: aioboto3.Session | None = None, region: str | None = None):
        settings = get_settings()
        self._session = session or aioboto3.Session()
        self._region = region or settings.aws_region

    async def describe_cluster(self, cluster_name: str) -> dict[str, Any]:
        """获取集群详细信息（原生 SageMaker 响应）.

        不捕获 botocore SDK 异常，裸抛由调用方（读穿透服务 → API 层）按降级策略处理。

        Raises:
            botocore.exceptions.ClientError: SageMaker API 调用失败（集群不存在、权限不足等）
            botocore.exceptions.EndpointConnectionError: 无法连接到 SageMaker 端点
        """
        async with self._session.client("sagemaker", region_name=self._region) as sm:
            response: dict[str, Any] = await sm.describe_cluster(ClusterName=cluster_name)
            return response


@lru_cache(maxsize=1)
def get_sagemaker_cluster_client() -> SageMakerClusterClient:
    """获取 SageMaker 集群客户端单例.

    使用 lru_cache 实现单例，避免重复创建 AWS 客户端。
    """
    return SageMakerClusterClient()
