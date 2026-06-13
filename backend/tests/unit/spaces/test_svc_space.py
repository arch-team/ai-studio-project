"""SpaceService 单元测试 - 真实 App 启停操作与状态懒同步.

平台契约: 状态以 SageMaker App（计算实例）为事实源——
停止必须 delete_app 释放实例，启动必须 create_app 拉起实例。
"""

from unittest.mock import AsyncMock

import pytest

from src.modules.spaces.application.services.space_service import SpaceService
from src.modules.spaces.domain.entities.space import Space
from src.modules.spaces.domain.exceptions import InvalidSpaceStateError, SpaceError
from src.modules.spaces.domain.repositories import ISpaceRepository
from src.modules.spaces.domain.value_objects import (
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.shared.domain.exceptions import InvalidStateTransitionError


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
    repo.update.side_effect = lambda space: space
    repo.create.side_effect = lambda space: space
    return repo


@pytest.fixture
def mock_sagemaker() -> AsyncMock:
    client = AsyncMock()
    client.create_space.return_value = {"name": "x", "arn": "arn:aws:sagemaker:::space/x", "status": "Pending"}
    client.create_app.return_value = {"arn": "arn:aws:sagemaker:::app/x", "status": "Pending"}
    client.delete_app.return_value = None
    client.describe_app.return_value = None
    return client


@pytest.fixture
def service(mock_repo: AsyncMock, mock_sagemaker: AsyncMock) -> SpaceService:
    """构造 SpaceService（使用 StudioSpaceBackend 包装 mock_sagemaker）。"""
    from src.modules.spaces.domain.value_objects import SpaceBackend
    from src.modules.spaces.infrastructure.external.studio_space_backend import StudioSpaceBackend

    # 将 mock_sagemaker 包进真实的 StudioSpaceBackend
    studio_backend = StudioSpaceBackend(sagemaker_client=mock_sagemaker)

    return SpaceService(
        space_repository=mock_repo,
        backends={SpaceBackend.STUDIO: studio_backend},
        quota_checker=None,  # 现有测试不涉及配额
    )


class TestCreateSpaceStartsApp:
    """创建空间必须同时拉起 App 计算实例."""

    async def test_create_space_calls_create_app(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        mock_repo.get_by_name_and_owner.return_value = None

        space = await service.create_space(
            owner_id=1,
            data={"space_name": "dev-1", "space_type": "jupyter", "instance_type": "ml.g5.xlarge"},
        )

        mock_sagemaker.create_space.assert_awaited_once()
        mock_sagemaker.create_app.assert_awaited_once()
        _, kwargs = mock_sagemaker.create_app.await_args
        assert kwargs["space_name"] == "dev-1"
        assert kwargs["ide_type"] == "jupyterlab"
        assert kwargs["instance_type"] == "ml.g5.xlarge"
        assert space.status == SpaceStatus.PENDING

    async def test_create_app_failure_cleans_up_sagemaker_space(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        mock_repo.get_by_name_and_owner.return_value = None
        mock_sagemaker.create_app.side_effect = SpaceError(message="quota exceeded")

        with pytest.raises(SpaceError):
            await service.create_space(owner_id=1, data={"space_name": "dev-2"})

        # 防止孤儿 SageMaker Space：失败时尽力清理
        mock_sagemaker.delete_space.assert_awaited_once_with("dev-2")
        mock_repo.create.assert_not_awaited()


class TestStopSpaceRealOperation:
    """停止空间必须 delete_app 真实释放计算实例."""

    async def test_stop_running_space_deletes_app(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("11111111-1111-1111-1111-111111111111", SpaceStatus.RUNNING)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = {"status": "InService"}

        result = await service.stop_space(space.id)

        mock_sagemaker.delete_app.assert_awaited_once()
        _, kwargs = mock_sagemaker.delete_app.await_args
        assert kwargs["space_name"] == space.space_name
        assert kwargs["ide_type"] == "jupyterlab"
        assert result.status == SpaceStatus.STOPPED

    async def test_stop_when_app_already_gone_is_idempotent(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        # DB 认为 running 但 App 已被外部停止：同步纠正后幂等返回，不再调 delete_app
        space = _make_space("22222222-2222-2222-2222-222222222222", SpaceStatus.RUNNING)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = None

        result = await service.stop_space(space.id)

        assert result.status == SpaceStatus.STOPPED
        mock_sagemaker.delete_app.assert_not_awaited()

    async def test_stop_pending_space_raises_conflict(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("33333333-3333-3333-3333-333333333333", SpaceStatus.PENDING)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = {"status": "Pending"}

        with pytest.raises(InvalidStateTransitionError):
            await service.stop_space(space.id)
        mock_sagemaker.delete_app.assert_not_awaited()


class TestStartSpaceRealOperation:
    """启动空间必须 create_app 真实拉起计算实例."""

    async def test_start_stopped_space_creates_app(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("44444444-4444-4444-4444-444444444444", SpaceStatus.STOPPED)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = None

        result = await service.start_space(space.id)

        mock_sagemaker.create_app.assert_awaited_once()
        _, kwargs = mock_sagemaker.create_app.await_args
        assert kwargs["space_name"] == space.space_name
        assert kwargs["ide_type"] == "jupyterlab"
        assert kwargs["instance_type"] == "ml.g5.xlarge"
        # App 拉起需要时间，先进入启动中
        assert result.status == SpaceStatus.PENDING

    async def test_start_when_app_already_running_is_idempotent(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("55555555-5555-5555-5555-555555555555", SpaceStatus.STOPPED)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = {"status": "InService"}

        result = await service.start_space(space.id)

        assert result.status == SpaceStatus.RUNNING
        mock_sagemaker.create_app.assert_not_awaited()

    async def test_start_when_app_still_starting_is_idempotent(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("66666666-6666-6666-6666-666666666666", SpaceStatus.PENDING)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = {"status": "Pending"}

        result = await service.start_space(space.id)

        assert result.status == SpaceStatus.PENDING
        mock_sagemaker.create_app.assert_not_awaited()


class TestDeleteSpaceRealOperation:
    """删除空间必须清理 App 后删除 SageMaker Space."""

    async def test_delete_stopped_space_deletes_app_then_space(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("77777777-7777-7777-7777-777777777777", SpaceStatus.STOPPED)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = None

        await service.delete_space(space.id)

        mock_sagemaker.delete_app.assert_awaited_once()
        mock_sagemaker.delete_space.assert_awaited_once_with(space.space_name)
        mock_repo.soft_delete.assert_awaited_once_with(space.id)


class TestStatusSyncFromApp:
    """状态懒同步以 App（计算实例）状态为事实源."""

    async def test_list_syncs_pending_to_running_when_app_inservice(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("88888888-8888-8888-8888-888888888888", SpaceStatus.PENDING)
        mock_repo.list_spaces.return_value = ([space], 1)
        mock_sagemaker.describe_app.return_value = {"status": "InService"}

        spaces, total = await service.list_spaces(owner_id=1)

        assert total == 1
        assert spaces[0].status == SpaceStatus.RUNNING
        mock_repo.update.assert_awaited_once()

    async def test_list_syncs_running_to_stopped_when_app_gone(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("99999999-9999-9999-9999-999999999999", SpaceStatus.RUNNING)
        mock_repo.list_spaces.return_value = ([space], 1)
        mock_sagemaker.describe_app.return_value = None

        spaces, _ = await service.list_spaces()

        assert spaces[0].status == SpaceStatus.STOPPED

    async def test_list_syncs_to_failed_when_app_failed(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", SpaceStatus.PENDING)
        mock_repo.list_spaces.return_value = ([space], 1)
        mock_sagemaker.describe_app.return_value = {"status": "Failed"}

        spaces, _ = await service.list_spaces()

        assert spaces[0].status == SpaceStatus.FAILED

    async def test_list_treats_deleted_app_as_stopped(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        # DeleteApp 后 App 元数据保留 24h（Status=Deleted），等价于无运行实例
        space = _make_space("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", SpaceStatus.RUNNING)
        mock_repo.list_spaces.return_value = ([space], 1)
        mock_sagemaker.describe_app.return_value = {"status": "Deleted"}

        spaces, _ = await service.list_spaces()

        assert spaces[0].status == SpaceStatus.STOPPED

    async def test_list_keeps_status_when_describe_fails(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("cccccccc-cccc-cccc-cccc-cccccccccccc", SpaceStatus.PENDING)
        mock_repo.list_spaces.return_value = ([space], 1)
        mock_sagemaker.describe_app.side_effect = RuntimeError("AWS timeout")

        spaces, total = await service.list_spaces()

        assert total == 1
        assert spaces[0].status == SpaceStatus.PENDING

    async def test_list_skips_describe_for_deleted_space(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("dddddddd-dddd-dddd-dddd-dddddddddddd", SpaceStatus.DELETED)
        mock_repo.list_spaces.return_value = ([space], 1)

        spaces, _ = await service.list_spaces()

        assert spaces[0].status == SpaceStatus.DELETED
        mock_sagemaker.describe_app.assert_not_awaited()

    async def test_get_space_syncs_from_app_status(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee", SpaceStatus.PENDING)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = {"status": "InService"}

        result = await service.get_space(space.id)

        assert result.status == SpaceStatus.RUNNING


class TestGetSpaceAccessUrl:
    """打开 IDE: 仅运行中的空间可签发 presigned 访问 URL."""

    async def test_running_space_returns_presigned_url(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("a1111111-1111-1111-1111-111111111111", SpaceStatus.RUNNING)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = {"status": "InService"}
        mock_sagemaker.create_presigned_url.return_value = "https://x.studio.us-east-1.sagemaker.aws/auth?token=t"

        url = await service.get_space_access_url(space.id)

        assert url.startswith("https://")
        _, kwargs = mock_sagemaker.create_presigned_url.await_args
        assert kwargs["space_name"] == space.space_name
        assert kwargs["ide_type"] == "jupyterlab"

    async def test_stopped_space_raises_conflict(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("a2222222-2222-2222-2222-222222222222", SpaceStatus.STOPPED)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = None

        with pytest.raises(InvalidSpaceStateError):
            await service.get_space_access_url(space.id)
        mock_sagemaker.create_presigned_url.assert_not_awaited()

    async def test_pending_space_raises_conflict(
        self, service: SpaceService, mock_repo: AsyncMock, mock_sagemaker: AsyncMock
    ) -> None:
        space = _make_space("a3333333-3333-3333-3333-333333333333", SpaceStatus.PENDING)
        mock_repo.get_by_id.return_value = space
        mock_sagemaker.describe_app.return_value = {"status": "Pending"}

        with pytest.raises(InvalidSpaceStateError):
            await service.get_space_access_url(space.id)


class TestBackendDispatch:
    """backend 策略分发和 HyperPod 配额校验."""

    async def test_create_hyperpod_calls_quota_then_hyperpod_backend(
        self, mock_repo: AsyncMock
    ) -> None:
        """HyperPod backend 创建时走配额检查，调用 hyperpod backend。"""
        from src.modules.spaces.application.interfaces import ISpaceBackendClient
        from src.modules.spaces.domain.value_objects import SpaceBackend
        from src.shared.domain.interfaces import IQuotaChecker

        # Mock backends
        mock_studio = AsyncMock(spec=ISpaceBackendClient)
        mock_hyperpod = AsyncMock(spec=ISpaceBackendClient)
        mock_hyperpod.provision_space.return_value = {
            "namespace": "team-a",
            "workspace_name": "dev-hyperpod-1",
        }

        # Mock quota checker: 配额充足
        mock_quota = AsyncMock(spec=IQuotaChecker)
        mock_quota.check_quota.return_value = True

        # 构造 service（新签名）
        service = SpaceService(
            space_repository=mock_repo,
            backends={SpaceBackend.STUDIO: mock_studio, SpaceBackend.HYPERPOD: mock_hyperpod},
            quota_checker=mock_quota,
        )

        mock_repo.get_by_name_and_owner.return_value = None

        # 创建 HyperPod space
        space = await service.create_space(
            owner_id=1,
            data={
                "space_name": "dev-hyperpod-1",
                "backend": "hyperpod",
                "instance_type": "ml.g5.xlarge",
                "namespace": "team-a",
                "queue_name": "default",
            },
        )

        # 验证配额检查被调用（resource_type="gpu", amount=1）
        mock_quota.check_quota.assert_awaited_once()
        _, kwargs = mock_quota.check_quota.await_args
        assert kwargs["resource_type"] == "gpu"
        assert kwargs["amount"] == 1

        # 验证 hyperpod backend 被调用
        mock_hyperpod.provision_space.assert_awaited_once()
        # 验证 studio backend 未被调用
        mock_studio.provision_space.assert_not_awaited()

        # 验证实体字段回填
        assert space.namespace == "team-a"
        assert space.space_name == "dev-hyperpod-1"

    async def test_create_hyperpod_quota_exceeded_raises_429(
        self, mock_repo: AsyncMock
    ) -> None:
        """HyperPod 配额不足时抛 SpaceQuotaExceededError，不调用 backend。"""
        from src.modules.spaces.application.interfaces import ISpaceBackendClient
        from src.modules.spaces.domain.exceptions import SpaceQuotaExceededError
        from src.modules.spaces.domain.value_objects import SpaceBackend
        from src.shared.domain.interfaces import IQuotaChecker

        mock_studio = AsyncMock(spec=ISpaceBackendClient)
        mock_hyperpod = AsyncMock(spec=ISpaceBackendClient)

        # Mock quota checker: 配额不足
        mock_quota = AsyncMock(spec=IQuotaChecker)
        mock_quota.check_quota.return_value = False
        mock_quota.get_available_quota.return_value = 0

        service = SpaceService(
            space_repository=mock_repo,
            backends={SpaceBackend.STUDIO: mock_studio, SpaceBackend.HYPERPOD: mock_hyperpod},
            quota_checker=mock_quota,
        )

        mock_repo.get_by_name_and_owner.return_value = None

        # 尝试创建 HyperPod space，期望抛 429
        with pytest.raises(SpaceQuotaExceededError) as exc_info:
            await service.create_space(
                owner_id=1,
                data={
                    "space_name": "dev-hyperpod-2",
                    "backend": "hyperpod",
                    "instance_type": "ml.g5.xlarge",
                },
            )

        # 验证异常细节
        assert exc_info.value.resource == "gpu"
        assert exc_info.value.required == 1
        assert exc_info.value.available == 0

        # 验证 provision_space 未被调用（配额不足时应提前中断）
        mock_hyperpod.provision_space.assert_not_awaited()

    async def test_create_studio_skips_quota(
        self, mock_repo: AsyncMock
    ) -> None:
        """Studio backend 创建时跳过配额检查。"""
        from src.modules.spaces.application.interfaces import ISpaceBackendClient
        from src.modules.spaces.domain.value_objects import SpaceBackend
        from src.shared.domain.interfaces import IQuotaChecker

        mock_studio = AsyncMock(spec=ISpaceBackendClient)
        mock_studio.provision_space.return_value = {"arn": "arn:aws:sagemaker:::space/dev-studio-1"}
        mock_hyperpod = AsyncMock(spec=ISpaceBackendClient)

        mock_quota = AsyncMock(spec=IQuotaChecker)

        service = SpaceService(
            space_repository=mock_repo,
            backends={SpaceBackend.STUDIO: mock_studio, SpaceBackend.HYPERPOD: mock_hyperpod},
            quota_checker=mock_quota,
        )

        mock_repo.get_by_name_and_owner.return_value = None

        # 创建 Studio space
        space = await service.create_space(
            owner_id=1,
            data={
                "space_name": "dev-studio-1",
                "backend": "studio",
                "instance_type": "ml.g5.xlarge",
            },
        )

        # 验证配额检查未被调用
        mock_quota.check_quota.assert_not_awaited()

        # 验证 studio backend 被调用
        mock_studio.provision_space.assert_awaited_once()

        # 验证实体 sagemaker_space_arn 被回填
        assert space.sagemaker_space_arn == "arn:aws:sagemaker:::space/dev-studio-1"
