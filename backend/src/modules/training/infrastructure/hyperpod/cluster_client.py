"""HyperPod 集群管理客户端。"""

import os
from typing import Any

import aioboto3
import structlog

logger = structlog.get_logger(__name__)

# 条件导入
try:
    from sagemaker.hyperpod import set_cluster_context
except ImportError:
    set_cluster_context = None

try:
    from kubernetes import config as k8s_config
except ImportError:
    k8s_config = None


def _mark_sdk_kubeconfig_loaded() -> None:
    """标记 HyperPod SDK 的 kubeconfig 已加载，跳过其内部的 load_kube_config()。

    SDK 的 verify_kube_config() 硬编码读取 kubeconfig 文件，
    in-cluster 场景（ServiceAccount token）下该文件不存在。
    """
    try:
        from sagemaker.hyperpod.training import HyperPodPytorchJob

        HyperPodPytorchJob.is_kubeconfig_loaded = True
    except ImportError:
        pass


class ClusterClient:
    """HyperPod 集群管理客户端。"""

    _cluster_contexts: set[str] = set()
    _incluster_loaded: bool = False

    def __init__(self, session: aioboto3.Session, region: str, default_cluster_name: str | None = None):
        self._session = session
        self._region = region
        self._default_cluster_name = default_cluster_name

    def _try_incluster_context(self) -> bool:
        """在 K8s Pod 内时加载 in-cluster 配置，成功返回 True。"""
        if ClusterClient._incluster_loaded:
            return True
        if not os.environ.get("KUBERNETES_SERVICE_HOST") or k8s_config is None:
            return False

        try:
            k8s_config.load_incluster_config()
            _mark_sdk_kubeconfig_loaded()
            ClusterClient._incluster_loaded = True
            logger.info("incluster_kube_config_loaded")
            return True
        except Exception as e:
            logger.warning("incluster_kube_config_failed", error=str(e))
            return False

    def ensure_cluster_context(self, cluster_name: str | None = None) -> None:
        """确保集群上下文已设置。

        优先级：in-cluster 配置（Pod 内） > SDK set_cluster_context（本地开发）。
        """
        # Pod 内直接用 ServiceAccount，不依赖 aws eks update-kubeconfig
        if self._try_incluster_context():
            return

        target_cluster = cluster_name or self._default_cluster_name

        if not target_cluster:
            logger.warning("no_cluster_name_for_context")
            return

        if target_cluster in self._cluster_contexts:
            return

        if set_cluster_context is None:
            logger.warning("set_cluster_context_unavailable")
            return

        try:
            logger.info("setting_cluster_context", cluster=target_cluster)
            set_cluster_context(target_cluster)
            self._cluster_contexts.add(target_cluster)
            logger.info("cluster_context_set", cluster=target_cluster)
        except Exception as e:
            logger.exception(
                "cluster_context_failed",
                cluster=target_cluster,
                error_type=type(e).__name__,
                error=str(e),
            )

    async def create_cluster(
        self, cluster_name: str, instance_groups: list[dict[str, Any]], vpc_config: dict[str, Any]
    ) -> dict[str, Any]:
        """创建新的 HyperPod 集群。"""
        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.create_cluster(
                ClusterName=cluster_name, InstanceGroups=instance_groups, VpcConfig=vpc_config
            )

    async def describe_cluster(self, cluster_name: str) -> dict[str, Any]:
        """获取集群详细信息。"""
        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.describe_cluster(ClusterName=cluster_name)

    async def list_clusters(self, max_results: int = 100, next_token: str | None = None) -> dict[str, Any]:
        """列出所有 HyperPod 集群。"""
        params: dict[str, Any] = {"MaxResults": max_results}
        if next_token:
            params["NextToken"] = next_token

        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.list_clusters(**params)

    async def delete_cluster(self, cluster_name: str) -> dict[str, Any]:
        """删除 HyperPod 集群。"""
        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.delete_cluster(ClusterName=cluster_name)

    async def update_cluster(self, cluster_name: str, instance_groups: list[dict[str, Any]]) -> dict[str, Any]:
        """更新集群实例组配置。"""
        async with self._session.client("sagemaker", region_name=self._region) as sagemaker:
            return await sagemaker.update_cluster(ClusterName=cluster_name, InstanceGroups=instance_groups)
