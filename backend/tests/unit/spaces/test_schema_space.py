"""Space API Schema 单元测试 - 不依赖数据库。

测试 CreateSpaceRequest 和 SpaceDetail 的 backend 字段映射。
"""

import pytest

from src.modules.spaces.api.schemas.requests import CreateSpaceRequest, SpaceBackendEnum
from src.modules.spaces.api.schemas.responses import SpaceDetail
from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.value_objects import SpaceBackend, SpaceInstanceType, SpaceStatus, SpaceType
from src.shared.utils import utc_now


class TestCreateSpaceRequestSchema:
    """CreateSpaceRequest schema 测试 - backend 字段支持。"""

    def test_default_backend_is_studio(self) -> None:
        """默认 backend 为 studio。"""
        request = CreateSpaceRequest(
            space_name="test-space",
            instance_type="ml.g5.xlarge",
        )
        assert request.backend == SpaceBackendEnum.STUDIO

    def test_backend_studio_is_valid(self) -> None:
        """backend="studio" 有效。"""
        request = CreateSpaceRequest(
            space_name="test-space",
            instance_type="ml.g5.xlarge",
            backend=SpaceBackendEnum.STUDIO,
        )
        assert request.backend == SpaceBackendEnum.STUDIO

    def test_backend_hyperpod_is_valid(self) -> None:
        """backend="hyperpod" 有效。"""
        request = CreateSpaceRequest(
            space_name="test-space",
            instance_type="ml.g5.xlarge",
            backend=SpaceBackendEnum.HYPERPOD,
        )
        assert request.backend == SpaceBackendEnum.HYPERPOD

    def test_invalid_backend_raises_validation_error(self) -> None:
        """无效的 backend 抛出验证错误。"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            CreateSpaceRequest(
                space_name="test-space",
                instance_type="ml.g5.xlarge",
                backend="invalid_backend",  # type: ignore[arg-type]
            )


class TestSpaceDetailSchema:
    """SpaceDetail schema 测试 - 包含 backend 和 HyperPod 字段。"""

    def test_from_entity_studio_space(self) -> None:
        """Studio Space 转 SpaceDetail - backend="studio", HyperPod 字段为 None。"""
        now = utc_now()
        space = Space(
            id="space-123",
            space_name="test-studio-space",
            owner_id=1,
            instance_type=SpaceInstanceType.ML_G5_XLARGE,
            space_type=SpaceType.JUPYTER,
            backend=SpaceBackend.STUDIO,
            storage_size_gb=20,
            status=SpaceStatus.RUNNING,
            sagemaker_space_arn="arn:aws:sagemaker:...",
            created_at=now,
            updated_at=now,
        )

        detail = SpaceDetail.from_entity(space)

        assert detail.id == "space-123"
        assert detail.space_name == "test-studio-space"
        assert detail.backend == SpaceBackendEnum.STUDIO
        assert detail.namespace is None
        assert detail.queue_name is None
        assert detail.workspace_template is None

    def test_from_entity_hyperpod_space(self) -> None:
        """HyperPod Space 转 SpaceDetail - backend="hyperpod", 包含 HyperPod 字段。"""
        now = utc_now()
        space = Space(
            id="space-456",
            space_name="test-hyperpod-space",
            owner_id=2,
            instance_type=SpaceInstanceType.ML_G5_2XLARGE,
            space_type=SpaceType.VSCODE,
            backend=SpaceBackend.HYPERPOD,
            namespace="team-ml",
            queue_name="gpu-queue",
            workspace_template="vscode-template",
            storage_size_gb=50,
            status=SpaceStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        detail = SpaceDetail.from_entity(space)

        assert detail.id == "space-456"
        assert detail.space_name == "test-hyperpod-space"
        assert detail.backend == SpaceBackendEnum.HYPERPOD
        assert detail.namespace == "team-ml"
        assert detail.queue_name == "gpu-queue"
        assert detail.workspace_template == "vscode-template"
