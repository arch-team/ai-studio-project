"""SpaceService 单元测试 - 列表/详情状态懒同步行为."""

from unittest.mock import AsyncMock

import pytest

from src.modules.spaces.application.services.space_service import SpaceService
from src.modules.spaces.domain.entities.space import Space
from src.modules.spaces.domain.repositories import ISpaceRepository
from src.modules.spaces.domain.value_objects import (
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)


def _make_space(space_id: str, status: SpaceStatus) -> Space:
    return Space(
        id=space_id,
        space_name=f"space-{space_id[:8]}",
        owner_id=1,
        instance_type=SpaceInstanceType.ML_G5_XLARGE,
        space_type=SpaceType.JUPYTER,
        storage_size_gb=10,
        status=status,
    )


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock(spec=ISpaceRepository)
    # update 原样返回传入实体，模拟持久化成功
    repo.update.side_effect = lambda space: space
    return repo


@pytest.fixture
def mock_sagemaker() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(mock_repo: AsyncMock, mock_sagemaker: AsyncMock) -> SpaceService:
    return SpaceService(
        space_repository=mock_repo,
        sagemaker_client=mock_sagemaker,
    )


class TestListSpacesLazySync:
    """list_spaces 必须将 SageMaker 实际状态对齐到返回结果."""

    async def test_list_spaces_syncs_pending_to_running(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("11111111-1111-1111-1111-111111111111", SpaceStatus.PENDING)
        mock_repo.list_spaces.return_value = ([space], 1)
        mock_sagemaker.describe_space.return_value = {"status": "InService"}

        spaces, total = await service.list_spaces(owner_id=1)

        assert total == 1
        assert spaces[0].status == SpaceStatus.RUNNING
        mock_repo.update.assert_awaited_once()

    async def test_list_spaces_keeps_status_when_sagemaker_matches(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("22222222-2222-2222-2222-222222222222", SpaceStatus.PENDING)
        mock_repo.list_spaces.return_value = ([space], 1)
        mock_sagemaker.describe_space.return_value = {"status": "Pending"}

        spaces, _ = await service.list_spaces()

        assert spaces[0].status == SpaceStatus.PENDING
        mock_repo.update.assert_not_awaited()

    async def test_list_spaces_survives_describe_failure(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("33333333-3333-3333-3333-333333333333", SpaceStatus.PENDING)
        mock_repo.list_spaces.return_value = ([space], 1)
        mock_sagemaker.describe_space.side_effect = RuntimeError("AWS timeout")

        spaces, total = await service.list_spaces()

        assert total == 1
        assert spaces[0].status == SpaceStatus.PENDING

    async def test_list_spaces_does_not_revert_stopped_to_running(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        # 平台层 stopped 是用户停用语义，SageMaker Space 本身仍 InService，不能回拉
        space = _make_space("44444444-4444-4444-4444-444444444444", SpaceStatus.STOPPED)
        mock_repo.list_spaces.return_value = ([space], 1)
        mock_sagemaker.describe_space.return_value = {"status": "InService"}

        spaces, _ = await service.list_spaces()

        assert spaces[0].status == SpaceStatus.STOPPED
        mock_repo.update.assert_not_awaited()

    async def test_list_spaces_skips_describe_for_deleted(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("55555555-5555-5555-5555-555555555555", SpaceStatus.DELETED)
        mock_repo.list_spaces.return_value = ([space], 1)

        spaces, _ = await service.list_spaces()

        assert spaces[0].status == SpaceStatus.DELETED
        mock_sagemaker.describe_space.assert_not_awaited()

    async def test_list_spaces_syncs_multiple_spaces(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        pending = _make_space("66666666-6666-6666-6666-666666666666", SpaceStatus.PENDING)
        running = _make_space("77777777-7777-7777-7777-777777777777", SpaceStatus.RUNNING)
        mock_repo.list_spaces.return_value = ([pending, running], 2)
        mock_sagemaker.describe_space.side_effect = [
            {"status": "InService"},  # pending → running
            {"status": "Failed"},  # running → failed
        ]

        spaces, total = await service.list_spaces()

        assert total == 2
        assert spaces[0].status == SpaceStatus.RUNNING
        assert spaces[1].status == SpaceStatus.FAILED


class TestGetSpaceLazySync:
    """get_space 既有懒同步行为回归."""

    async def test_get_space_syncs_pending_to_running(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("88888888-8888-8888-8888-888888888888", SpaceStatus.PENDING)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_space.return_value = {"status": "InService"}

        result = await service.get_space(space.id)

        assert result.status == SpaceStatus.RUNNING
