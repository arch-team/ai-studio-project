"""StudioSpaceBackend 适配器测试 —— 验证 Studio 编排被正确封装。"""

from unittest.mock import AsyncMock, call

import pytest

from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.value_objects import (
    SpaceBackend,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.modules.spaces.infrastructure.external.studio_space_backend import (
    StudioSpaceBackend,
)


def _studio_space() -> Space:
    return Space(
        id="s-1",
        space_name="dev-1",
        owner_id=1,
        backend=SpaceBackend.STUDIO,
        instance_type=SpaceInstanceType.ML_G5_XLARGE,
        space_type=SpaceType.JUPYTER,
        status=SpaceStatus.PENDING,
    )


@pytest.fixture
def mock_sagemaker() -> AsyncMock:
    client = AsyncMock()
    client.create_space.return_value = {"arn": "arn:aws:sagemaker:::space/x"}
    client.create_app.return_value = {"arn": "arn:aws:sagemaker:::app/x"}
    client.describe_app.return_value = {"status": "InService"}
    client.create_presigned_url.return_value = "https://x.studio.us-east-1.sagemaker.aws/..."
    return client


class TestProvision:
    async def test_provision_calls_create_space_then_app(self, mock_sagemaker: AsyncMock) -> None:
        backend = StudioSpaceBackend(mock_sagemaker)
        result = await backend.provision_space(_studio_space())
        mock_sagemaker.create_space.assert_awaited_once()
        mock_sagemaker.create_app.assert_awaited_once()
        assert "arn" in result

    async def test_provision_orphan_cleanup_on_app_failure(self, mock_sagemaker: AsyncMock) -> None:
        mock_sagemaker.create_app.side_effect = RuntimeError("boom")
        backend = StudioSpaceBackend(mock_sagemaker)
        with pytest.raises(RuntimeError):
            await backend.provision_space(_studio_space())
        mock_sagemaker.delete_space.assert_awaited_once()


class TestDescribe:
    async def test_describe_maps_inservice_to_running(self, mock_sagemaker: AsyncMock) -> None:
        backend = StudioSpaceBackend(mock_sagemaker)
        result = await backend.describe_space(_studio_space())
        assert result == {"status": SpaceStatus.RUNNING.value}

    async def test_describe_no_app_returns_stopped(self, mock_sagemaker: AsyncMock) -> None:
        # App 不存在 = 无运行实例 = 明确"已停止"
        mock_sagemaker.describe_app.return_value = None
        backend = StudioSpaceBackend(mock_sagemaker)
        result = await backend.describe_space(_studio_space())
        assert result == {"status": SpaceStatus.STOPPED.value}

    @pytest.mark.parametrize(
        "app_status,expected",
        [
            ("Pending", SpaceStatus.PENDING.value),
            ("InService", SpaceStatus.RUNNING.value),
            ("Deleting", SpaceStatus.STOPPED.value),
            ("Failed", SpaceStatus.FAILED.value),
        ],
    )
    async def test_describe_maps_app_status_to_platform_status(
        self, mock_sagemaker: AsyncMock, app_status: str, expected: str
    ) -> None:
        mock_sagemaker.describe_app.return_value = {"status": app_status}
        backend = StudioSpaceBackend(mock_sagemaker)
        result = await backend.describe_space(_studio_space())
        assert result == {"status": expected}

    async def test_describe_unmapped_status_returns_none(self, mock_sagemaker: AsyncMock) -> None:
        # 未知状态无法映射 → 返回 None（下游视为"不变更状态"）
        mock_sagemaker.describe_app.return_value = {"status": "WeirdStatus"}
        backend = StudioSpaceBackend(mock_sagemaker)
        result = await backend.describe_space(_studio_space())
        assert result is None


class TestStart:
    async def test_start_calls_create_app_with_args(self, mock_sagemaker: AsyncMock) -> None:
        backend = StudioSpaceBackend(mock_sagemaker)
        await backend.start_space(_studio_space())
        mock_sagemaker.create_app.assert_awaited_once_with(
            space_name="dev-1",
            ide_type="jupyterlab",
            instance_type="ml.g5.xlarge",
            lifecycle_config_arn=None,
        )


class TestStop:
    async def test_stop_calls_delete_app_with_args(self, mock_sagemaker: AsyncMock) -> None:
        backend = StudioSpaceBackend(mock_sagemaker)
        await backend.stop_space(_studio_space())
        mock_sagemaker.delete_app.assert_awaited_once_with(
            space_name="dev-1",
            ide_type="jupyterlab",
        )


class TestDelete:
    async def test_delete_calls_delete_app_then_delete_space(self, mock_sagemaker: AsyncMock) -> None:
        backend = StudioSpaceBackend(mock_sagemaker)
        await backend.delete_space(_studio_space())
        # 先清理 App 再删除 Space，验证调用顺序
        assert mock_sagemaker.mock_calls == [
            call.delete_app(space_name="dev-1", ide_type="jupyterlab"),
            call.delete_space("dev-1"),
        ]


class TestAccessUrl:
    async def test_create_access_url_delegates_to_presigned_url(self, mock_sagemaker: AsyncMock) -> None:
        backend = StudioSpaceBackend(mock_sagemaker)
        result = await backend.create_access_url(_studio_space(), conn_type="web-ui")
        mock_sagemaker.create_presigned_url.assert_awaited_once_with(
            space_name="dev-1",
            ide_type="jupyterlab",
        )
        assert result == "https://x.studio.us-east-1.sagemaker.aws/..."
