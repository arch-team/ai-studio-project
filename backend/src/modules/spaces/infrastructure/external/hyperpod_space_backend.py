"""HyperPod Spaces 后端适配器 —— 将 K8sWorkspaceClient 适配为 ISpaceBackendClient。

通过 Kubernetes CRD 操作 HyperPod 原生 Spaces (workspace.jupyter.org/v1alpha1 Workspace)。
"""

import asyncio
from typing import Any

import structlog

from src.modules.spaces.application.interfaces import ISpaceBackendClient
from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.exceptions import HyperPodSpaceBackendError
from src.modules.spaces.domain.value_objects import map_workspace_status
from src.modules.spaces.infrastructure.external.k8s_workspace_client import (
    K8sWorkspaceClient,
)
from src.modules.spaces.infrastructure.external.workspace_crd import (
    CONNECTION_API_VERSION_FULL,
    CONNECTION_KIND,
    WORKSPACE_API_VERSION_FULL,
    WORKSPACE_KIND,
)

logger = structlog.get_logger(__name__)

# 交互空间优先级类 (设计 §5.2: 优先级 100)
INTERACTIVE_SPACE_PRIORITY_CLASS = "interactive-space-priority"

# Access URL 轮询配置
_MAX_POLL_ATTEMPTS = 10
_POLL_INTERVAL_SECONDS = 1.0


class HyperPodSpaceBackend(ISpaceBackendClient):
    """HyperPod Spaces 后端实现,封装 Kubernetes CRD 操作。"""

    def __init__(self, k8s_client: K8sWorkspaceClient) -> None:
        self._k8s = k8s_client

    async def provision_space(self, space: Space) -> dict[str, Any]:
        """创建 Workspace CRD 并设置 desiredStatus=Running。

        Returns:
            包含 namespace 和 workspace_name 的字典
        """
        body = self._build_workspace_body(space)

        await self._k8s.create_workspace(
            namespace=space.namespace or "default",
            name=space.space_name,
            body=body,
        )

        logger.info(
            "hyperpod_workspace_created",
            workspace_name=space.space_name,
            namespace=space.namespace,
            queue_name=space.queue_name,
        )

        return {
            "namespace": space.namespace,
            "workspace_name": space.space_name,
        }

    async def delete_space(self, space: Space) -> None:
        """删除 Workspace CRD (幂等)。"""
        await self._k8s.delete_workspace(
            namespace=space.namespace or "default",
            name=space.space_name,
        )

        logger.info(
            "hyperpod_workspace_deleted",
            workspace_name=space.space_name,
            namespace=space.namespace,
        )

    async def start_space(self, space: Space) -> None:
        """拉起 Workspace 计算实例 (patch desiredStatus=Running)。"""
        await self._k8s.patch_workspace_desired_status(
            namespace=space.namespace or "default",
            name=space.space_name,
            desired_status="Running",
        )

        logger.info(
            "hyperpod_workspace_started",
            workspace_name=space.space_name,
            namespace=space.namespace,
        )

    async def stop_space(self, space: Space) -> None:
        """释放 Workspace 计算实例 (patch desiredStatus=Stopped)。"""
        await self._k8s.patch_workspace_desired_status(
            namespace=space.namespace or "default",
            name=space.space_name,
            desired_status="Stopped",
        )

        logger.info(
            "hyperpod_workspace_stopped",
            workspace_name=space.space_name,
            namespace=space.namespace,
        )

    async def describe_space(self, space: Space) -> dict[str, Any] | None:
        """查询 Workspace 状态并映射为平台状态。

        三态返回契约 (与 StudioSpaceBackend 对称):
        - CRD 不存在 → {"status": "stopped"} (明确"已停止")
        - phase 可映射 → {"status": <SpaceStatus 值>}
        - phase 无法映射 → None (无可用状态信息,下游不变更状态)
        """
        workspace = await self._k8s.get_workspace(
            namespace=space.namespace or "default",
            name=space.space_name,
        )

        # CRD 不存在 = 无运行实例 = 已停止
        if workspace is None:
            return {"status": "stopped"}

        # 映射 Workspace phase 到平台状态
        phase = workspace.get("status", {}).get("phase")
        mapped = map_workspace_status(phase)

        if mapped:
            return {"status": mapped.value}

        # 未知/无法映射的状态: 返回 None,下游视为"不变更状态"
        logger.warning(
            "unmapped_workspace_phase",
            phase=phase,
            workspace_name=space.space_name,
            namespace=space.namespace,
        )
        return None

    async def create_access_url(self, space: Space, conn_type: str) -> str:
        """签发免登录访问 URL (创建 WorkspaceConnection 并轮询获取 URL)。

        Args:
            space: 空间实体
            conn_type: 连接类型 (web-ui | vscode-remote)

        Returns:
            免登录访问 URL

        Raises:
            HyperPodSpaceBackendError: 超时或无法获取 URL
        """
        connection_name = f"{space.space_name}-{conn_type}"
        body = self._build_workspace_connection_body(space, conn_type, connection_name)

        # 创建 WorkspaceConnection CRD
        await self._k8s.create_workspace_connection(
            namespace=space.namespace or "default",
            body=body,
        )

        # 轮询获取 workspaceConnectionUrl
        for attempt in range(_MAX_POLL_ATTEMPTS):
            connection = await self._k8s.get_workspace_connection(
                namespace=space.namespace or "default",
                name=connection_name,
            )

            if connection:
                url: str | None = connection.get("status", {}).get("workspaceConnectionUrl")
                if url:
                    logger.info(
                        "workspace_connection_url_ready",
                        workspace_name=space.space_name,
                        conn_type=conn_type,
                        attempts=attempt + 1,
                    )
                    return url

            if attempt < _MAX_POLL_ATTEMPTS - 1:
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)

        # 超时
        raise HyperPodSpaceBackendError(
            message=(
                f"Timeout waiting for access URL after {_MAX_POLL_ATTEMPTS} attempts "
                f"(workspace={space.space_name}, type={conn_type})"
            )
        )

    def _build_workspace_body(self, space: Space) -> dict[str, Any]:
        """构建 Workspace CRD body。"""
        resources = space.get_resource_requirements()

        return {
            "apiVersion": WORKSPACE_API_VERSION_FULL,
            "kind": WORKSPACE_KIND,
            "metadata": {
                "name": space.space_name,
                "labels": {
                    "kueue.x-k8s.io/queue-name": space.queue_name or "default-queue",
                    "kueue.x-k8s.io/priority-class": INTERACTIVE_SPACE_PRIORITY_CLASS,
                },
            },
            "spec": {
                "desiredStatus": "Running",
                "templateRef": {
                    "name": space.workspace_template or "default-template",
                },
                "resources": {
                    "requests": {
                        # K8s CPU 单位: 核数 (整数字符串, 如 "4" = 4 核)
                        "cpu": str(resources["cpu_cores"]),
                        # K8s 内存单位: Gi (1Gi = 2^30 字节)
                        "memory": f"{resources['memory_gb']}Gi",
                    },
                    "limits": {
                        # GPU 通过 nvidia.com/gpu 扩展资源声明 (整数张数)
                        "nvidia.com/gpu": str(resources["gpu_count"]),
                    },
                },
            },
        }

    def _build_workspace_connection_body(
        self,
        space: Space,
        conn_type: str,
        connection_name: str,
    ) -> dict[str, Any]:
        """构建 WorkspaceConnection CRD body。"""
        return {
            "apiVersion": CONNECTION_API_VERSION_FULL,
            "kind": CONNECTION_KIND,
            "metadata": {
                "name": connection_name,
            },
            "spec": {
                "workspaceName": space.space_name,
                "workspaceConnectionType": conn_type,
            },
        }
