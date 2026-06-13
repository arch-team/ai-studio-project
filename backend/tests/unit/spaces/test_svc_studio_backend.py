"""StudioSpaceBackend 适配器测试 —— 验证 Studio 编排被正确封装。"""

from unittest.mock import AsyncMock

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
        assert result["status"] == SpaceStatus.RUNNING.value
