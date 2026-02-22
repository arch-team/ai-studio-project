"""Kueue 队列状态查询客户端。

通过 K8s API 查询 Kueue Workload 状态，用于训练任务调试页面。
使用 httpx 调用 Kubernetes API Server。

部署环境从 Pod 挂载的 ServiceAccount token 读取认证信息。
开发环境（无 K8s 集群）gracefully 降级返回 None。
"""

from pathlib import Path
from typing import Any

import httpx
import structlog

from src.modules.training.application.interfaces import KueueWorkloadData

logger = structlog.get_logger(__name__)

# K8s ServiceAccount token 挂载路径
_SA_TOKEN_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
_SA_CA_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
_K8S_HOST_ENV = "KUBERNETES_SERVICE_HOST"
_K8S_PORT_ENV = "KUBERNETES_SERVICE_PORT"

# Kueue API 路径
_KUEUE_API_GROUP = "kueue.x-k8s.io"
_KUEUE_API_VERSION = "v1beta1"


class KueueClient:
    """Kueue 队列状态查询客户端。"""

    def __init__(
        self,
        k8s_api_url: str | None = None,
        token: str | None = None,
    ) -> None:
        self._k8s_api_url = k8s_api_url
        self._token = token

    async def get_workload_status(
        self,
        workload_name: str,
        namespace: str = "training-jobs",
    ) -> KueueWorkloadData | None:
        """从 Kueue API 获取 Workload 状态。

        Returns:
            Workload 状态数据，不可用时返回 None
        """
        api_url = self._resolve_api_url()
        if api_url is None:
            logger.info("kueue_k8s_api_unavailable", workload_name=workload_name)
            return None

        token = self._resolve_token()
        url = (
            f"{api_url}/apis/{_KUEUE_API_GROUP}/{_KUEUE_API_VERSION}"
            f"/namespaces/{namespace}/workloads/{workload_name}"
        )

        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            verify = str(_SA_CA_PATH) if _SA_CA_PATH.exists() else False
            async with httpx.AsyncClient(verify=verify, timeout=10.0) as client:
                response = await client.get(url, headers=headers)

            if response.status_code == 404:
                logger.info("kueue_workload_not_found", workload_name=workload_name, namespace=namespace)
                return None

            response.raise_for_status()
            data = response.json()
            return self._parse_workload(data, workload_name, namespace)

        except httpx.ConnectError:
            logger.info("kueue_k8s_connection_failed", workload_name=workload_name)
            return None
        except Exception as e:
            logger.warning("kueue_api_error", workload_name=workload_name, error=str(e))
            return None

    def _resolve_api_url(self) -> str | None:
        """解析 K8s API Server URL。"""
        if self._k8s_api_url:
            return self._k8s_api_url

        import os

        host = os.environ.get(_K8S_HOST_ENV)
        port = os.environ.get(_K8S_PORT_ENV, "443")
        if host:
            return f"https://{host}:{port}"

        return None

    def _resolve_token(self) -> str | None:
        """解析 ServiceAccount token。"""
        if self._token:
            return self._token

        if _SA_TOKEN_PATH.exists():
            return _SA_TOKEN_PATH.read_text().strip()

        return None

    def _parse_workload(
        self,
        data: dict[str, Any],
        workload_name: str,
        namespace: str,
    ) -> KueueWorkloadData:
        """解析 Kueue Workload API 响应。"""
        status = data.get("status", {})
        conditions = status.get("conditions", [])

        # 从 conditions 提取状态标志
        admitted = self._check_condition(conditions, "Admitted")
        quota_reserved = self._check_condition(conditions, "QuotaReserved")
        pods_ready = self._check_condition(conditions, "PodsReady")
        evicted = self._check_condition(conditions, "Evicted")
        finished = self._check_condition(conditions, "Finished")

        # 提取 admission 信息
        admission_data = status.get("admission")
        local_queue: str | None = None
        cluster_queue: str | None = None
        if admission_data:
            cluster_queue = admission_data.get("clusterQueue")
        # localQueue 在 spec 中
        spec = data.get("spec", {})
        local_queue = spec.get("queueName")

        # 序列化条件列表
        parsed_conditions = [
            {
                "type": c.get("type", ""),
                "status": c.get("status", ""),
                "lastTransitionTime": c.get("lastTransitionTime"),
                "reason": c.get("reason"),
                "message": c.get("message"),
            }
            for c in conditions
        ]

        return KueueWorkloadData(
            workload_name=workload_name,
            namespace=namespace,
            admitted=admitted,
            quota_reserved=quota_reserved,
            pods_ready=pods_ready,
            evicted=evicted,
            finished=finished,
            local_queue=local_queue,
            cluster_queue=cluster_queue,
            conditions=parsed_conditions if parsed_conditions else None,
            admission=admission_data,
        )

    @staticmethod
    def _check_condition(conditions: list[dict[str, Any]], condition_type: str) -> bool:
        """检查指定条件是否为 True。"""
        for condition in conditions:
            if condition.get("type") == condition_type:
                return condition.get("status") == "True"
        return False
