"""测试 Dataset 领域实体。"""

import pytest

from src.shared.domain.exceptions import InvalidStateTransitionError


class TestDatasetCreation:
    """测试 Dataset 实体创建。"""

    def test_create_valid_dataset(self) -> None:
        """创建有效数据集。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        dataset = Dataset(
            id=1,
            name="imagenet-2012",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/datasets/imagenet",
            dataset_type=DatasetType.IMAGE,
            owner_id=100,
        )

        assert dataset.id == 1
        assert dataset.name == "imagenet-2012"
        assert dataset.version == "v1"  # 默认版本
        assert dataset.storage_type == DatasetStorageType.FSX
        assert dataset.storage_uri == "/fsx/datasets/imagenet"
        assert dataset.dataset_type == DatasetType.IMAGE
        assert dataset.owner_id == 100
        assert dataset.visibility == DatasetVisibility.PRIVATE  # 默认私有
        assert dataset.status == DatasetStatus.PREPARING  # 默认准备中

    def test_create_dataset_with_optional_fields(self) -> None:
        """创建带可选字段的数据集。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        dataset = Dataset(
            id=2,
            name="coco-2017",
            description="COCO 2017 目标检测数据集",
            version="v2",
            storage_type=DatasetStorageType.S3,
            storage_uri="s3://ml-datasets/coco-2017",
            total_size_bytes=100_000_000_000,
            file_count=330_000,
            dataset_type=DatasetType.IMAGE,
            data_format="coco",
            tags=["cv", "detection", "coco"],
            visibility=DatasetVisibility.PUBLIC,
            owner_id=100,
            status=DatasetStatus.AVAILABLE,
        )

        assert dataset.description == "COCO 2017 目标检测数据集"
        assert dataset.version == "v2"
        assert dataset.total_size_bytes == 100_000_000_000
        assert dataset.file_count == 330_000
        assert dataset.data_format == "coco"
        assert dataset.tags == ["cv", "detection", "coco"]
        assert dataset.visibility == DatasetVisibility.PUBLIC
        assert dataset.status == DatasetStatus.AVAILABLE


class TestDatasetStatusTransitions:
    """测试 Dataset 状态转换逻辑。"""

    def test_can_transition_from_preparing_to_available(self) -> None:
        """可以从 PREPARING 转换到 AVAILABLE。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.PREPARING,
        )

        assert dataset.can_transition_to(DatasetStatus.AVAILABLE) is True

    def test_can_transition_from_preparing_to_error(self) -> None:
        """可以从 PREPARING 转换到 ERROR。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.PREPARING,
        )

        assert dataset.can_transition_to(DatasetStatus.ERROR) is True

    def test_cannot_transition_from_preparing_to_archived(self) -> None:
        """不能从 PREPARING 直接转换到 ARCHIVED。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.PREPARING,
        )

        assert dataset.can_transition_to(DatasetStatus.ARCHIVED) is False

    def test_transition_to_valid_state(self) -> None:
        """转换到有效状态成功。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.PREPARING,
        )

        dataset.transition_to(DatasetStatus.AVAILABLE)
        assert dataset.status == DatasetStatus.AVAILABLE

    def test_transition_to_invalid_state_raises_error(self) -> None:
        """转换到无效状态抛出异常。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.PREPARING,
        )

        with pytest.raises(InvalidStateTransitionError):
            dataset.transition_to(DatasetStatus.ARCHIVED)


class TestDatasetConvenienceMethods:
    """测试 Dataset 便捷方法。"""

    def test_mark_available(self) -> None:
        """mark_available 方法正常工作。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.PREPARING,
        )

        dataset.mark_available()
        assert dataset.status == DatasetStatus.AVAILABLE

    def test_mark_error(self) -> None:
        """mark_error 方法正常工作。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.PREPARING,
        )

        dataset.mark_error()
        assert dataset.status == DatasetStatus.ERROR

    def test_archive(self) -> None:
        """archive 方法正常工作。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.AVAILABLE,
        )

        dataset.archive()
        assert dataset.status == DatasetStatus.ARCHIVED

    def test_restore(self) -> None:
        """restore 方法正常工作。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.ARCHIVED,
        )

        dataset.restore()
        assert dataset.status == DatasetStatus.AVAILABLE


class TestDatasetAccessControl:
    """测试 Dataset 访问控制。"""

    def test_is_public(self) -> None:
        """验证 is_public 方法。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        public_dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            visibility=DatasetVisibility.PUBLIC,
        )

        private_dataset = Dataset(
            id=2,
            name="test2",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test2",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            visibility=DatasetVisibility.PRIVATE,
        )

        assert public_dataset.is_public() is True
        assert private_dataset.is_public() is False

    def test_is_accessible_by_owner(self) -> None:
        """所有者可以访问自己的数据集。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=100,
            visibility=DatasetVisibility.PRIVATE,
        )

        assert dataset.is_accessible_by(user_id=100) is True

    def test_public_dataset_accessible_by_anyone(self) -> None:
        """公开数据集所有人可访问。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=100,
            visibility=DatasetVisibility.PUBLIC,
        )

        assert dataset.is_accessible_by(user_id=200) is True

    def test_private_dataset_not_accessible_by_others(self) -> None:
        """私有数据集他人不可访问。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStorageType,
            DatasetType,
            DatasetVisibility,
        )

        dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=100,
            visibility=DatasetVisibility.PRIVATE,
        )

        assert dataset.is_accessible_by(user_id=200) is False


class TestDatasetStateQueries:
    """测试 Dataset 状态查询方法。"""

    def test_is_available(self) -> None:
        """验证 is_available 方法。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        available_dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.AVAILABLE,
        )

        preparing_dataset = Dataset(
            id=2,
            name="test2",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test2",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.PREPARING,
        )

        assert available_dataset.is_available() is True
        assert preparing_dataset.is_available() is False

    def test_is_archived(self) -> None:
        """验证 is_archived 方法。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        archived_dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.ARCHIVED,
        )

        assert archived_dataset.is_archived() is True

    def test_has_error(self) -> None:
        """验证 has_error 方法。"""
        from src.modules.datasets.domain.entities import Dataset
        from src.modules.datasets.domain.value_objects import (
            DatasetStatus,
            DatasetStorageType,
            DatasetType,
        )

        error_dataset = Dataset(
            id=1,
            name="test",
            storage_type=DatasetStorageType.FSX,
            storage_uri="/fsx/test",
            dataset_type=DatasetType.TEXT,
            owner_id=1,
            status=DatasetStatus.ERROR,
        )

        assert error_dataset.has_error() is True
