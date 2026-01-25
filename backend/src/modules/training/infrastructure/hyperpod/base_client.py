"""HyperPod 客户端基类 - 提供通用功能和辅助方法"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T")

# 条件导入 HyperPod SDK
try:
    from sagemaker.hyperpod import set_cluster_context
    from sagemaker.hyperpod.training import HyperPodPytorchJob

    HYPERPOD_SDK_AVAILABLE = True
except ImportError:
    set_cluster_context = None
    HyperPodPytorchJob = None
    HYPERPOD_SDK_AVAILABLE = False


class HyperPodBaseClient:
    """HyperPod 客户端基类，提供通用功能"""

    # 已设置上下文的集群缓存 (避免重复设置)
    _cluster_contexts: set[str] = set()

    def __init__(self, region: str = "us-east-1", default_cluster_name: str | None = None):
        """初始化基础客户端

        Args:
            region: AWS 区域
            default_cluster_name: 默认集群名称
        """
        self._region = region
        self._default_cluster_name = default_cluster_name

    def _ensure_sdk_available(self) -> None:
        """确保 HyperPod SDK 可用

        Raises:
            HyperPodSDKUnavailableError: SDK 不可用时抛出
        """
        if not HYPERPOD_SDK_AVAILABLE:
            from src.modules.training.domain.exceptions import HyperPodSDKUnavailableError

            raise HyperPodSDKUnavailableError()

    def _ensure_cluster_context(self, cluster_name: str | None = None) -> None:
        """确保集群上下文已设置

        HyperPod SDK 需要先调用 set_cluster_context() 配置 kubeconfig。

        Args:
            cluster_name: 集群名称，如果为 None 则使用默认集群
        """
        target_cluster = cluster_name or self._default_cluster_name

        if not target_cluster:
            logger.warning("No cluster name provided for context setup")
            return

        # 检查是否已设置此集群的上下文
        if target_cluster in self._cluster_contexts:
            return

        if set_cluster_context is None:
            logger.warning("set_cluster_context not available, SDK status operations may fail")
            return

        try:
            logger.info(f"Setting cluster context for: {target_cluster}")
            set_cluster_context(target_cluster)
            self._cluster_contexts.add(target_cluster)
            logger.info(f"Cluster context set successfully: {target_cluster}")
        except Exception as e:
            logger.error(
                f"Failed to set cluster context for {target_cluster}: {type(e).__name__}: {e}",
                exc_info=True,
            )

    async def _run_in_executor(self, func: Callable[[], T]) -> T:
        """在线程池中运行同步函数

        注意: 此方法仅用于 HyperPod SDK 操作，因为 sagemaker-hyperpod SDK 没有异步版本。
        对于 SageMaker API 和 S3 操作，应使用 aioboto3 原生异步。

        Args:
            func: 要执行的同步函数

        Returns:
            函数执行结果
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func)

    def _build_env_list(self, env_dict: dict[str, Any] | None) -> list[Any] | None:
        """构建环境变量列表

        Args:
            env_dict: 环境变量字典

        Returns:
            环境变量配置列表
        """
        if not env_dict:
            return None

        from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import Env

        return [Env(name=k, value=str(v)) for k, v in env_dict.items()]

    def _build_kueue_labels(self, queue_name: str | None, priority_class: str | None) -> dict[str, str]:
        """构建 Kueue 调度标签

        Args:
            queue_name: Kueue 队列名称
            priority_class: 优先级类名称

        Returns:
            Kubernetes 标签字典
        """
        labels: dict[str, str] = {}
        if queue_name:
            labels["kueue.x-k8s.io/queue-name"] = queue_name
        if priority_class:
            labels["kueue.x-k8s.io/priority-class"] = priority_class
        return labels

    def _map_status(self, hyperpod_status: str) -> str:
        """映射 HyperPod 状态到平台标准状态

        Args:
            hyperpod_status: HyperPod/Kubernetes 状态

        Returns:
            平台标准状态
        """
        from src.modules.training.domain.value_objects.constants import HYPERPOD_STATUS_MAPPING

        return HYPERPOD_STATUS_MAPPING.get(hyperpod_status, "unknown")