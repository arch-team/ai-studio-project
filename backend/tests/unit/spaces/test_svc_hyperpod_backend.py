"""HyperPodSpaceBackend 测试 —— mock K8sWorkspaceClient 验证 CRD body 与状态映射。

CRD schema 对齐真实集群 (Phase B Task 15 核验):
- status 用 conditions 列表 (非 phase 字段)
- 访问 URL 在 Workspace 自身 status.accessURL (无独立 WorkspaceConnection CRD)
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.exceptions import HyperPodSpaceBackendError
from src.modules.spaces.domain.value_objects import (
    SpaceBackend,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.modules.spaces.infrastructure.external.hyperpod_space_backend import (
    INTERACTIVE_SPACE_PRIORITY_CLASS,
    HyperPodSpaceBackend,
)


def _hp_space() -> Space:
    return Space(
        id="h-1",
        space_name="dev-hp",
        owner_id=1,
        backend=SpaceBackend.HYPERPOD,
        instance_type=SpaceInstanceType.ML_G5_XLARGE,
        space_type=SpaceType.JUPYTER,
        namespace="dev-spaces",
        queue_name="team-alpha-localqueue",
        workspace_template="sagemaker-jupyter-template",
        status=SpaceStatus.PENDING,
    )


def _conditions(**types: str) -> list[dict[str, str]]:
    return [{"type": t, "status": s} for t, s in types.items()]


@pytest.fixture
def mock_k8s() -> AsyncMock:
    k8s = AsyncMock()
    k8s.create_workspace.return_value = {"metadata": {"name": "dev-hp"}}
    k8s.get_workspace.return_value = {"status": {"conditions": _conditions(Available="True", Progressing="False")}}
    return k8s


class TestProvision:
    async def test_provision_sets_kueue_labels_and_desired_running(self, mock_k8s: AsyncMock) -> None:
        """测试 provision 生成正确的 CRD body: kueue 标签、desired status、resource requirements。"""
        backend = HyperPodSpaceBackend(mock_k8s)
        result = await backend.provision_space(_hp_space())

        # 验证 CRD body
        body = mock_k8s.create_workspace.call_args.kwargs["body"]
        labels = body["metadata"]["labels"]
        assert labels["kueue.x-k8s.io/queue-name"] == "team-alpha-localqueue"
        assert labels["kueue.x-k8s.io/priority-class"] == INTERACTIVE_SPACE_PRIORITY_CLASS
        assert body["spec"]["desiredStatus"] == "Running"

        # displayName 是真实 CRD 必填字段
        assert body["spec"]["displayName"] == "dev-hp"

        # templateRef 含 name + namespace (真实 CRD 模板在 jupyter-k8s-system)
        assert body["spec"]["templateRef"]["name"] == "sagemaker-jupyter-template"
        assert body["spec"]["templateRef"]["namespace"] == "jupyter-k8s-system"

        # 验证 resource requirements
        resources = body["spec"]["resources"]
        assert resources["requests"]["cpu"] == "4"
        assert resources["requests"]["memory"] == "16Gi"
        assert resources["limits"]["nvidia.com/gpu"] == "1"

        # 验证返回值
        assert result["namespace"] == "dev-spaces"
        assert result["workspace_name"] == "dev-hp"

    async def test_provision_calls_create_workspace_with_correct_params(self, mock_k8s: AsyncMock) -> None:
        """测试 provision 调用 create_workspace 时使用正确的 namespace 和 name。"""
        backend = HyperPodSpaceBackend(mock_k8s)
        await backend.provision_space(_hp_space())

        call_args = mock_k8s.create_workspace.call_args
        assert call_args.kwargs["namespace"] == "dev-spaces"
        assert call_args.kwargs["name"] == "dev-hp"


class TestLifecycle:
    async def test_start_patches_desired_running(self, mock_k8s: AsyncMock) -> None:
        """测试 start_space patch desired status 为 Running。"""
        backend = HyperPodSpaceBackend(mock_k8s)
        await backend.start_space(_hp_space())

        mock_k8s.patch_workspace_desired_status.assert_awaited_once()
        call_args = mock_k8s.patch_workspace_desired_status.call_args
        assert call_args.kwargs["namespace"] == "dev-spaces"
        assert call_args.kwargs["name"] == "dev-hp"
        assert call_args.kwargs["desired_status"] == "Running"

    async def test_stop_patches_desired_stopped(self, mock_k8s: AsyncMock) -> None:
        """测试 stop_space patch desired status 为 Stopped。"""
        backend = HyperPodSpaceBackend(mock_k8s)
        await backend.stop_space(_hp_space())

        mock_k8s.patch_workspace_desired_status.assert_awaited_once()
        assert mock_k8s.patch_workspace_desired_status.call_args.kwargs["desired_status"] == "Stopped"

    async def test_delete_calls_delete_workspace(self, mock_k8s: AsyncMock) -> None:
        """测试 delete_space 调用 delete_workspace。"""
        backend = HyperPodSpaceBackend(mock_k8s)
        await backend.delete_space(_hp_space())

        mock_k8s.delete_workspace.assert_awaited_once_with(
            namespace="dev-spaces",
            name="dev-hp",
        )


class TestDescribe:
    async def test_describe_maps_available_to_running(self, mock_k8s: AsyncMock) -> None:
        """测试 describe_space 映射 Available=True 到 RUNNING 状态。"""
        mock_k8s.get_workspace.return_value = {
            "status": {"conditions": _conditions(Available="True", Progressing="False")}
        }
        backend = HyperPodSpaceBackend(mock_k8s)

        result = await backend.describe_space(_hp_space())
        assert result == {"status": SpaceStatus.RUNNING.value}

    async def test_describe_maps_progressing_to_pending(self, mock_k8s: AsyncMock) -> None:
        """测试 describe_space 映射 Progressing=True 到 PENDING 状态。"""
        mock_k8s.get_workspace.return_value = {
            "status": {"conditions": _conditions(Available="False", Progressing="True")}
        }
        backend = HyperPodSpaceBackend(mock_k8s)

        result = await backend.describe_space(_hp_space())
        assert result == {"status": SpaceStatus.PENDING.value}

    async def test_describe_returns_stopped_when_workspace_not_exists(self, mock_k8s: AsyncMock) -> None:
        """测试 describe_space 在 CRD 不存在时返回 stopped (三态契约)。"""
        mock_k8s.get_workspace.return_value = None
        backend = HyperPodSpaceBackend(mock_k8s)

        result = await backend.describe_space(_hp_space())
        assert result == {"status": SpaceStatus.STOPPED.value}

    async def test_describe_returns_none_when_conditions_unmappable(self, mock_k8s: AsyncMock) -> None:
        """测试 describe_space 在 conditions 全 Unknown 时返回 None (三态契约)。"""
        mock_k8s.get_workspace.return_value = {
            "status": {"conditions": _conditions(Available="Unknown", Progressing="Unknown")}
        }
        backend = HyperPodSpaceBackend(mock_k8s)

        result = await backend.describe_space(_hp_space())
        assert result is None


class TestAccessUrl:
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_create_access_url_polls_workspace_access_url(
        self, mock_sleep: AsyncMock, mock_k8s: AsyncMock
    ) -> None:
        """测试 create_access_url 轮询 Workspace status.accessURL (mock sleep 瞬时完成)。"""
        # 第一次无 accessURL,第二次有
        mock_k8s.get_workspace.side_effect = [
            {"status": {"conditions": _conditions(Available="False", Progressing="True")}},
            {
                "status": {
                    "conditions": _conditions(Available="True"),
                    "accessURL": "https://ide.dev.example.com/lab",
                }
            },
        ]

        backend = HyperPodSpaceBackend(mock_k8s)
        url = await backend.create_access_url(_hp_space(), conn_type="web-ui")

        # 轮询 Workspace 自身 (非独立 connection CRD)
        assert mock_k8s.get_workspace.call_count == 2
        assert url == "https://ide.dev.example.com/lab"

    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_create_access_url_times_out_after_max_retries(
        self, mock_sleep: AsyncMock, mock_k8s: AsyncMock
    ) -> None:
        """测试 create_access_url 在超过最大轮询次数后超时 (mock sleep 瞬时完成)。"""
        # 始终无 accessURL
        mock_k8s.get_workspace.return_value = {
            "status": {"conditions": _conditions(Available="False", Progressing="True")}
        }

        backend = HyperPodSpaceBackend(mock_k8s)

        with pytest.raises(HyperPodSpaceBackendError, match="Timeout waiting for access URL after 10 attempts"):
            await backend.create_access_url(_hp_space(), conn_type="web-ui")

    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_create_access_url_handles_none_workspace(self, mock_sleep: AsyncMock, mock_k8s: AsyncMock) -> None:
        """测试 create_access_url 处理 get_workspace 返回 None (mock sleep 瞬时完成)。"""
        mock_k8s.get_workspace.return_value = None

        backend = HyperPodSpaceBackend(mock_k8s)

        with pytest.raises(HyperPodSpaceBackendError, match="Timeout waiting for access URL after 10 attempts"):
            await backend.create_access_url(_hp_space(), conn_type="web-ui")
