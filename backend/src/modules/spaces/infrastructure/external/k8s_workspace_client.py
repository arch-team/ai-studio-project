"""Kubernetes Workspace CRD 客户端。

通过 K8s API 操作 workspace.jupyter.org/v1alpha1 Workspace CRD。
使用 httpx 调用 Kubernetes API Server。

部署环境从 Pod 挂载的 ServiceAccount token 读取认证信息。
开发环境（无 K8s 集群）读操作 gracefully 降级返回 None，写操作抛 SpaceBackendUnavailableError。

注意 (Phase B Task 15 核验): 真实 add-on 无独立 WorkspaceConnection CRD,
访问 URL 在 Workspace 自身 status.accessURL,故本客户端仅操作 Workspace 资源。
"""

import os
from pathlib import Path
from typing import Any

import httpx
import structlog

from src.modules.spaces.domain.exceptions import (
    HyperPodSpaceBackendError,
    SpaceBackendUnavailableError,
)
from src.modules.spaces.infrastructure.external.workspace_crd import (
    WORKSPACE_API_GROUP as _WORKSPACE_API_GROUP,
)
from src.modules.spaces.infrastructure.external.workspace_crd import (
    WORKSPACE_API_VERSION as _WORKSPACE_API_VERSION,
)

logger = structlog.get_logger(__name__)

# K8s ServiceAccount token 挂载路径
_SA_TOKEN_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
_SA_CA_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
_K8S_HOST_ENV = "KUBERNETES_SERVICE_HOST"
_K8S_PORT_ENV = "KUBERNETES_SERVICE_PORT"

# CRD API group/version 常量从 workspace_crd 模块导入 (见上方 import 别名)
# URL path 构造逻辑保持不变 (_WORKSPACE_API_GROUP 等仍可用)


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
        url_path = f"/apis/{_WORKSPACE_API_GROUP}/{_WORKSPACE_API_VERSION}/namespaces/{namespace}/workspaces"

        # 写操作：无集群→SpaceBackendUnavailableError，连接失败→HyperPodSpaceBackendError
        response = await self._request("POST", url_path, json=body)
        assert response is not None  # 写操作不降级，_request 必返回 Response
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning(
                "workspace_create_failed",
                namespace=namespace,
                name=name,
                status_code=e.response.status_code,
            )
            raise HyperPodSpaceBackendError(message=f"Failed to create workspace: {e.response.status_code}") from e
        data: dict[str, Any] = response.json()
        return data

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
        url_path = f"/apis/{_WORKSPACE_API_GROUP}/{_WORKSPACE_API_VERSION}/namespaces/{namespace}/workspaces/{name}"

        # 读操作降级：无集群/连接失败→None
        response = await self._request("GET", url_path, allow_unavailable=True, allow_connect_error=True)
        if response is None:
            return None

        if response.status_code == 404:
            logger.info("workspace_not_found", namespace=namespace, name=name)
            return None

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning(
                "workspace_get_failed",
                namespace=namespace,
                name=name,
                status_code=e.response.status_code,
            )
            raise HyperPodSpaceBackendError(message=f"Failed to get workspace: {e.response.status_code}") from e
        data: dict[str, Any] = response.json()
        return data

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
        url_path = f"/apis/{_WORKSPACE_API_GROUP}/{_WORKSPACE_API_VERSION}/namespaces/{namespace}/workspaces/{name}"
        body = {"spec": {"desiredStatus": desired_status}}

        # 写操作：无集群→SpaceBackendUnavailableError，连接失败→HyperPodSpaceBackendError
        response = await self._request(
            "PATCH",
            url_path,
            json=body,
            extra_headers={"Content-Type": "application/merge-patch+json"},
        )
        assert response is not None  # 写操作不降级，_request 必返回 Response
        try:
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
        url_path = f"/apis/{_WORKSPACE_API_GROUP}/{_WORKSPACE_API_VERSION}/namespaces/{namespace}/workspaces/{name}"

        # 无集群→幂等返回（无可删资源）；连接失败→抛异常（allow_connect_error=False）
        response = await self._request("DELETE", url_path, allow_unavailable=True)
        if response is None:
            logger.info("workspace_delete_skipped_no_cluster", namespace=namespace, name=name)
            return

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # 幂等成功
                logger.info("workspace_already_deleted", namespace=namespace, name=name)
                return
            logger.warning(
                "workspace_delete_failed",
                namespace=namespace,
                name=name,
                status_code=e.response.status_code,
            )
            raise HyperPodSpaceBackendError(message=f"Failed to delete workspace: {e.response.status_code}") from e

    async def _request(
        self,
        method: str,
        url_path: str,
        *,
        json: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
        allow_unavailable: bool = False,
        allow_connect_error: bool = False,
    ) -> httpx.Response | None:
        """统一发出 K8s API 请求，封装可用性检查、认证、CA 验证与连接错误处理。

        不在此处理 HTTP 状态码（如 404/raise_for_status），由调用方按语义处理。

        Args:
            method: HTTP 方法 (GET/POST/PATCH/DELETE)
            url_path: API 路径 (以 / 开头，不含 host)
            json: 请求体
            extra_headers: 附加请求头（如 merge-patch Content-Type）
            allow_unavailable: 无集群配置（无 api_url）时的降级开关。
                True → 返回 None（读操作降级 / delete 无可删资源）；
                False → 抛 SpaceBackendUnavailableError（写操作必须明确报错）。
            allow_connect_error: 连接失败（httpx.ConnectError）时的降级开关。
                True → 返回 None（读操作降级）；
                False → 抛 HyperPodSpaceBackendError（写操作/delete 连接失败须报错）。

        Returns:
            httpx.Response；降级场景下返回 None

        Raises:
            SpaceBackendUnavailableError: 无 api_url 且 allow_unavailable=False
            HyperPodSpaceBackendError: 连接失败且 allow_connect_error=False，或其它请求异常
        """
        api_url = self._resolve_api_url()
        if api_url is None:
            if allow_unavailable:
                logger.info("workspace_k8s_api_unavailable", url_path=url_path)
                return None
            raise SpaceBackendUnavailableError(message="K8s API unavailable: cluster not configured")

        token = self._resolve_token()
        headers = self._build_headers(token)
        if extra_headers:
            headers.update(extra_headers)

        url = f"{api_url}{url_path}"
        verify = str(_SA_CA_PATH) if _SA_CA_PATH.exists() else False

        try:
            async with httpx.AsyncClient(verify=verify, timeout=10.0) as client:
                # 按 method 显式分派：写操作（POST/PATCH）携带请求体，读/删操作不带
                if method == "POST":
                    return await client.post(url, json=json, headers=headers)
                if method == "PATCH":
                    return await client.patch(url, json=json, headers=headers)
                if method == "DELETE":
                    return await client.delete(url, headers=headers)
                return await client.get(url, headers=headers)
        except httpx.ConnectError:
            if allow_connect_error:
                logger.info("workspace_k8s_connection_failed", url_path=url_path)
                return None
            raise HyperPodSpaceBackendError(message="K8s API connection failed") from None
        except Exception as e:
            # 其它传输层异常（如超时）：读操作降级→None，写/删操作→HyperPodSpaceBackendError
            if allow_connect_error:
                logger.warning("workspace_api_error", url_path=url_path, error=str(e))
                return None
            logger.error("workspace_api_error", url_path=url_path, error=str(e))
            raise HyperPodSpaceBackendError(message=f"Workspace API error: {e}") from e

    def _resolve_api_url(self) -> str | None:
        """解析 K8s API Server URL。"""
        if self._k8s_api_url:
            return self._k8s_api_url

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
