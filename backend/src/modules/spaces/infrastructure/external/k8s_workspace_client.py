"""Kubernetes Workspace CRD 客户端。

通过 K8s API 操作 workspace.jupyter.org/v1alpha1 Workspace 和
connection.workspace.jupyter.org/v1alpha1 WorkspaceConnection CRD。
使用 httpx 调用 Kubernetes API Server。

部署环境从 Pod 挂载的 ServiceAccount token 读取认证信息。
开发环境（无 K8s 集群）读操作 gracefully 降级返回 None，写操作抛 SpaceBackendUnavailableError。
"""

from pathlib import Path
from typing import Any

import httpx
import structlog

from src.modules.spaces.domain.exceptions import (
    HyperPodSpaceBackendError,
    SpaceBackendUnavailableError,
)

logger = structlog.get_logger(__name__)

# K8s ServiceAccount token 挂载路径
_SA_TOKEN_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
_SA_CA_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
_K8S_HOST_ENV = "KUBERNETES_SERVICE_HOST"
_K8S_PORT_ENV = "KUBERNETES_SERVICE_PORT"

# Workspace CRD API 路径
_WORKSPACE_API_GROUP = "workspace.jupyter.org"
_WORKSPACE_API_VERSION = "v1alpha1"
_CONNECTION_API_GROUP = "connection.workspace.jupyter.org"
_CONNECTION_API_VERSION = "v1alpha1"


class K8sWorkspaceClient:
    """Kubernetes Workspace CRD 客户端。"""

    def __init__(
        self,
        k8s_api_url: str | None = None,
        token: str | None = None,
    ) -> None:
        self._k8s_api_url = k8s_api_url
        self._token = token

    async def create_workspace(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        """创建 Workspace。

        Args:
            namespace: K8s namespace
            name: Workspace 名称
            body: Workspace 资源定义 (包含 spec)

        Returns:
            创建后的 Workspace 资源

        Raises:
            SpaceBackendUnavailableError: K8s API 不可达
            HyperPodSpaceBackendError: 创建失败
        """
        api_url = self._resolve_api_url()
        if api_url is None:
            raise SpaceBackendUnavailableError(message="K8s API unavailable: cannot create workspace without cluster")

        token = self._resolve_token()
        url = f"{api_url}/apis/{_WORKSPACE_API_GROUP}/{_WORKSPACE_API_VERSION}" f"/namespaces/{namespace}/workspaces"

        headers = self._build_headers(token)

        try:
            verify = str(_SA_CA_PATH) if _SA_CA_PATH.exists() else False
            async with httpx.AsyncClient(verify=verify, timeout=10.0) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                return data
        except httpx.HTTPStatusError as e:
            logger.warning(
                "workspace_create_failed",
                namespace=namespace,
                name=name,
                status_code=e.response.status_code,
            )
            raise HyperPodSpaceBackendError(message=f"Failed to create workspace: {e.response.status_code}") from e
        except Exception as e:
            logger.error("workspace_api_error", namespace=namespace, name=name, error=str(e))
            raise HyperPodSpaceBackendError(message=f"Workspace API error: {e}") from e

    async def get_workspace(
        self,
        namespace: str,
        name: str,
    ) -> dict[str, Any] | None:
        """获取 Workspace。

        Args:
            namespace: K8s namespace
            name: Workspace 名称

        Returns:
            Workspace 资源，不存在或不可用时返回 None
        """
        api_url = self._resolve_api_url()
        if api_url is None:
            logger.info("workspace_k8s_api_unavailable", namespace=namespace, name=name)
            return None

        token = self._resolve_token()
        url = (
            f"{api_url}/apis/{_WORKSPACE_API_GROUP}/{_WORKSPACE_API_VERSION}"
            f"/namespaces/{namespace}/workspaces/{name}"
        )

        headers = self._build_headers(token)

        try:
            verify = str(_SA_CA_PATH) if _SA_CA_PATH.exists() else False
            async with httpx.AsyncClient(verify=verify, timeout=10.0) as client:
                response = await client.get(url, headers=headers)

            if response.status_code == 404:
                logger.info("workspace_not_found", namespace=namespace, name=name)
                return None

            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data

        except httpx.ConnectError:
            logger.info("workspace_k8s_connection_failed", namespace=namespace, name=name)
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(
                "workspace_get_failed",
                namespace=namespace,
                name=name,
                status_code=e.response.status_code,
            )
            raise HyperPodSpaceBackendError(message=f"Failed to get workspace: {e.response.status_code}") from e
        except Exception as e:
            logger.warning("workspace_api_error", namespace=namespace, name=name, error=str(e))
            return None

    async def patch_workspace_desired_status(
        self,
        namespace: str,
        name: str,
        desired_status: str,
    ) -> None:
        """更新 Workspace desiredStatus。

        使用 merge-patch 策略更新 spec.desiredStatus 字段。

        Args:
            namespace: K8s namespace
            name: Workspace 名称
            desired_status: 目标状态 (Running/Stopped)

        Raises:
            SpaceBackendUnavailableError: K8s API 不可达
            HyperPodSpaceBackendError: 更新失败
        """
        api_url = self._resolve_api_url()
        if api_url is None:
            raise SpaceBackendUnavailableError(message="K8s API unavailable: cannot patch workspace without cluster")

        token = self._resolve_token()
        url = (
            f"{api_url}/apis/{_WORKSPACE_API_GROUP}/{_WORKSPACE_API_VERSION}"
            f"/namespaces/{namespace}/workspaces/{name}"
        )

        headers = self._build_headers(token)
        headers["Content-Type"] = "application/merge-patch+json"

        body = {"spec": {"desiredStatus": desired_status}}

        try:
            verify = str(_SA_CA_PATH) if _SA_CA_PATH.exists() else False
            async with httpx.AsyncClient(verify=verify, timeout=10.0) as client:
                response = await client.patch(url, json=body, headers=headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning(
                "workspace_patch_failed",
                namespace=namespace,
                name=name,
                desired_status=desired_status,
                status_code=e.response.status_code,
            )
            raise HyperPodSpaceBackendError(message=f"Failed to patch workspace: {e.response.status_code}") from e
        except Exception as e:
            logger.error(
                "workspace_api_error",
                namespace=namespace,
                name=name,
                desired_status=desired_status,
                error=str(e),
            )
            raise HyperPodSpaceBackendError(message=f"Workspace API error: {e}") from e

    async def delete_workspace(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """删除 Workspace。

        404 视为幂等成功。无 API URL 时视为无可删资源（幂等成功）。

        Args:
            namespace: K8s namespace
            name: Workspace 名称

        Raises:
            HyperPodSpaceBackendError: 删除失败
        """
        api_url = self._resolve_api_url()
        if api_url is None:
            # 无集群配置，无可删资源，视为幂等成功
            logger.info("workspace_delete_skipped_no_cluster", namespace=namespace, name=name)
            return

        token = self._resolve_token()
        url = (
            f"{api_url}/apis/{_WORKSPACE_API_GROUP}/{_WORKSPACE_API_VERSION}"
            f"/namespaces/{namespace}/workspaces/{name}"
        )

        headers = self._build_headers(token)

        try:
            verify = str(_SA_CA_PATH) if _SA_CA_PATH.exists() else False
            async with httpx.AsyncClient(verify=verify, timeout=10.0) as client:
                response = await client.delete(url, headers=headers)

            if response.status_code == 404:
                # 幂等成功
                logger.info("workspace_already_deleted", namespace=namespace, name=name)
                return

            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                logger.warning(
                    "workspace_delete_failed",
                    namespace=namespace,
                    name=name,
                    status_code=e.response.status_code,
                )
                raise HyperPodSpaceBackendError(message=f"Failed to delete workspace: {e.response.status_code}") from e
        except Exception as e:
            logger.error("workspace_api_error", namespace=namespace, name=name, error=str(e))
            raise HyperPodSpaceBackendError(message=f"Workspace API error: {e}") from e

    async def create_workspace_connection(
        self,
        namespace: str,
        body: dict[str, Any],
    ) -> dict[str, Any] | None:
        """创建 WorkspaceConnection。

        Args:
            namespace: K8s namespace
            body: WorkspaceConnection 资源定义

        Returns:
            创建后的 WorkspaceConnection 资源

        Raises:
            SpaceBackendUnavailableError: K8s API 不可达
            HyperPodSpaceBackendError: 创建失败
        """
        api_url = self._resolve_api_url()
        if api_url is None:
            raise SpaceBackendUnavailableError(message="K8s API unavailable: cannot create connection without cluster")

        token = self._resolve_token()
        url = (
            f"{api_url}/apis/{_CONNECTION_API_GROUP}/{_CONNECTION_API_VERSION}"
            f"/namespaces/{namespace}/workspaceconnections"
        )

        headers = self._build_headers(token)

        try:
            verify = str(_SA_CA_PATH) if _SA_CA_PATH.exists() else False
            async with httpx.AsyncClient(verify=verify, timeout=10.0) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                return data
        except httpx.HTTPStatusError as e:
            logger.warning(
                "workspace_connection_create_failed",
                namespace=namespace,
                status_code=e.response.status_code,
            )
            raise HyperPodSpaceBackendError(message=f"Failed to create connection: {e.response.status_code}") from e
        except Exception as e:
            logger.error("workspace_connection_api_error", namespace=namespace, error=str(e))
            raise HyperPodSpaceBackendError(message=f"Connection API error: {e}") from e

    async def get_workspace_connection(
        self,
        namespace: str,
        name: str,
    ) -> dict[str, Any] | None:
        """获取 WorkspaceConnection。

        Args:
            namespace: K8s namespace
            name: Connection 名称

        Returns:
            Connection 资源，不存在或不可用时返回 None
        """
        api_url = self._resolve_api_url()
        if api_url is None:
            logger.info("workspace_connection_k8s_api_unavailable", namespace=namespace, name=name)
            return None

        token = self._resolve_token()
        url = (
            f"{api_url}/apis/{_CONNECTION_API_GROUP}/{_CONNECTION_API_VERSION}"
            f"/namespaces/{namespace}/workspaceconnections/{name}"
        )

        headers = self._build_headers(token)

        try:
            verify = str(_SA_CA_PATH) if _SA_CA_PATH.exists() else False
            async with httpx.AsyncClient(verify=verify, timeout=10.0) as client:
                response = await client.get(url, headers=headers)

            if response.status_code == 404:
                logger.info("workspace_connection_not_found", namespace=namespace, name=name)
                return None

            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data

        except httpx.ConnectError:
            logger.info("workspace_connection_k8s_connection_failed", namespace=namespace, name=name)
            return None
        except Exception as e:
            logger.warning("workspace_connection_api_error", namespace=namespace, name=name, error=str(e))
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

    def _build_headers(self, token: str | None) -> dict[str, str]:
        """构建 HTTP 请求头。"""
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
