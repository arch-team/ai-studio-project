"""K8sWorkspaceClient 测试 —— mock httpx 验证 CRD 请求构造。"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.modules.spaces.domain.exceptions import (
    HyperPodSpaceBackendError,
    SpaceBackendUnavailableError,
)
from src.modules.spaces.infrastructure.external.k8s_workspace_client import (
    K8sWorkspaceClient,
)


@pytest.fixture
def client() -> K8sWorkspaceClient:
    return K8sWorkspaceClient(k8s_api_url="https://k8s.test", token="tok")


class TestCreateWorkspace:
    async def test_posts_to_workspaces_endpoint(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            inst.post = AsyncMock(return_value=MagicMock(status_code=201, json=lambda: {"metadata": {"name": "w1"}}))
            inst.post.return_value.raise_for_status = MagicMock()
            await client.create_workspace(
                namespace="dev-spaces",
                name="w1",
                body={"spec": {"desiredStatus": "Running"}},
            )
            url = inst.post.call_args[0][0]
            assert "/apis/workspace.jupyter.org/v1alpha1/namespaces/dev-spaces/workspaces" in url

    async def test_no_api_url_raises_unavailable_error(self) -> None:
        c = K8sWorkspaceClient(k8s_api_url=None, token=None)
        with pytest.raises(SpaceBackendUnavailableError):
            await c.create_workspace("dev", "w1", {})


class TestGetWorkspace:
    async def test_404_returns_none(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            inst.get = AsyncMock(return_value=MagicMock(status_code=404))
            result = await client.get_workspace("dev-spaces", "missing")
            assert result is None

    async def test_connect_error_returns_none(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            inst.get = AsyncMock(side_effect=httpx.ConnectError("connection failed"))
            result = await client.get_workspace("dev-spaces", "w1")
            assert result is None

    async def test_no_api_url_returns_none(self) -> None:
        c = K8sWorkspaceClient(k8s_api_url=None, token=None)
        result = await c.get_workspace("dev-spaces", "w1")
        assert result is None

    async def test_api_error_raises_backend_error(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            response = MagicMock(status_code=500)
            response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError("500", request=MagicMock(), response=response)
            )
            inst.get = AsyncMock(return_value=response)
            with pytest.raises(HyperPodSpaceBackendError):
                await client.get_workspace("dev-spaces", "w1")


class TestPatchWorkspaceDesiredStatus:
    async def test_uses_merge_patch_content_type(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            inst.patch = AsyncMock(return_value=MagicMock(status_code=200))
            inst.patch.return_value.raise_for_status = MagicMock()
            await client.patch_workspace_desired_status("dev", "w1", "Running")
            headers = inst.patch.call_args[1]["headers"]
            assert headers["Content-Type"] == "application/merge-patch+json"

    async def test_no_api_url_raises_unavailable_error(self) -> None:
        c = K8sWorkspaceClient(k8s_api_url=None, token=None)
        with pytest.raises(SpaceBackendUnavailableError):
            await c.patch_workspace_desired_status("dev", "w1", "Running")


class TestDeleteWorkspace:
    async def test_404_is_idempotent(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            inst.delete = AsyncMock(return_value=MagicMock(status_code=404))
            # 不应抛异常
            await client.delete_workspace("dev-spaces", "missing")

    async def test_no_api_url_is_idempotent(self) -> None:
        c = K8sWorkspaceClient(k8s_api_url=None, token=None)
        # 删除不存在的资源视为成功
        await c.delete_workspace("dev", "w1")


class TestCreateWorkspaceConnection:
    async def test_posts_to_connections_endpoint(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            inst.post = AsyncMock(return_value=MagicMock(status_code=201, json=lambda: {"metadata": {"name": "conn1"}}))
            inst.post.return_value.raise_for_status = MagicMock()
            await client.create_workspace_connection("dev-spaces", {})
            url = inst.post.call_args[0][0]
            assert "/apis/connection.workspace.jupyter.org/v1alpha1/namespaces/dev-spaces/workspaceconnections" in url

    async def test_no_api_url_raises_unavailable_error(self) -> None:
        c = K8sWorkspaceClient(k8s_api_url=None, token=None)
        with pytest.raises(SpaceBackendUnavailableError):
            await c.create_workspace_connection("dev", {})


class TestGetWorkspaceConnection:
    async def test_404_returns_none(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            inst.get = AsyncMock(return_value=MagicMock(status_code=404))
            result = await client.get_workspace_connection("dev-spaces", "missing")
            assert result is None

    async def test_no_api_url_returns_none(self) -> None:
        c = K8sWorkspaceClient(k8s_api_url=None, token=None)
        result = await c.get_workspace_connection("dev-spaces", "conn1")
        assert result is None


class TestUnavailable:
    async def test_no_api_url_returns_none_for_reads(self) -> None:
        c = K8sWorkspaceClient(k8s_api_url=None, token=None)
        # 读操作降级返回 None
        result = await c.get_workspace("dev-spaces", "w1")
        assert result is None

    async def test_no_api_url_raises_for_writes(self) -> None:
        c = K8sWorkspaceClient(k8s_api_url=None, token=None)
        # 写操作在无集群时必须明确报错
        with pytest.raises(SpaceBackendUnavailableError):
            await c.create_workspace("dev", "w1", {})
