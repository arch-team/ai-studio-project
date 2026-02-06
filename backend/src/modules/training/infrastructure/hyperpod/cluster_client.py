"""HyperPod 集群管理客户端 - 专注于集群操作"""

from typing import Any

import aioboto3


class HyperPodClusterClient:
    """HyperPod 集群管理客户端

    职责：
    - 创建/删除集群
    - 查询集群状态
    - 更新集群配置
    - 列出所有集群
    """

    def __init__(self, region: str = "us-east-1"):
        """初始化集群客户端

        Args:
            region: AWS 区域
        """
        self._region = region
        self._session = aioboto3.Session()

    async def create_cluster(
        self,
        cluster_name: str,
        instance_groups: list[dict[str, Any]],
        vpc_config: dict[str, Any],
    ) -> dict[str, Any]:
        """创建新的 HyperPod 集群

        Args:
            cluster_name: 集群名称
            instance_groups: 实例组配置列表
            vpc_config: VPC 配置

        Returns:
            创建结果
        """
        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.create_cluster(
                ClusterName=cluster_name,
                InstanceGroups=instance_groups,
                VpcConfig=vpc_config,
            )

    async def describe_cluster(self, cluster_name: str) -> dict[str, Any]:
        """获取集群详细信息

        Args:
            cluster_name: 集群名称

        Returns:
            集群详细信息
        """
        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.describe_cluster(ClusterName=cluster_name)

    async def list_clusters(self, max_results: int = 100, next_token: str | None = None) -> dict[str, Any]:
        """列出所有 HyperPod 集群

        Args:
            max_results: 最大返回数量
            next_token: 分页令牌

        Returns:
            集群列表
        """
        params: dict[str, Any] = {"MaxResults": max_results}
        if next_token:
            params["NextToken"] = next_token

        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.list_clusters(**params)

    async def delete_cluster(self, cluster_name: str) -> dict[str, Any]:
        """删除 HyperPod 集群

        Args:
            cluster_name: 集群名称

        Returns:
            删除结果
        """
        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.delete_cluster(ClusterName=cluster_name)

    async def update_cluster(self, cluster_name: str, instance_groups: list[dict[str, Any]]) -> dict[str, Any]:
        """更新集群实例组配置

        Args:
            cluster_name: 集群名称
            instance_groups: 新的实例组配置

        Returns:
            更新结果
        """
        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.update_cluster(
                ClusterName=cluster_name,
                InstanceGroups=instance_groups,
            )

    async def get_cluster_status(self, cluster_name: str) -> str:
        """获取集群状态

        Args:
            cluster_name: 集群名称

        Returns:
            集群状态字符串
        """
        cluster_info = await self.describe_cluster(cluster_name)
        return cluster_info.get("ClusterStatus", "Unknown")
