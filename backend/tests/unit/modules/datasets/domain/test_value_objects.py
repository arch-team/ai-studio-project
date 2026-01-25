"""测试 Dataset 值对象（枚举类型）。"""

import pytest
from enum import Enum


class TestDatasetStorageType:
    """测试 DatasetStorageType 枚举。"""

    def test_storage_type_values(self) -> None:
        """验证存储类型枚举值。"""
        from src.modules.datasets.domain.value_objects import DatasetStorageType

        assert DatasetStorageType.FSX.value == "FSX"
        assert DatasetStorageType.S3.value == "S3"
        assert DatasetStorageType.EFS.value == "EFS"

    def test_storage_type_is_enum(self) -> None:
        """验证是 Enum 类型。"""
        from src.modules.datasets.domain.value_objects import DatasetStorageType

        assert issubclass(DatasetStorageType, Enum)

    def test_storage_type_count(self) -> None:
        """验证枚举值数量。"""
        from src.modules.datasets.domain.value_objects import DatasetStorageType

        assert len(DatasetStorageType) == 3


class TestDatasetType:
    """测试 DatasetType 枚举。"""

    def test_dataset_type_values(self) -> None:
        """验证数据集类型枚举值。"""
        from src.modules.datasets.domain.value_objects import DatasetType

        assert DatasetType.IMAGE.value == "IMAGE"
        assert DatasetType.TEXT.value == "TEXT"
        assert DatasetType.AUDIO.value == "AUDIO"
        assert DatasetType.VIDEO.value == "VIDEO"
        assert DatasetType.TABULAR.value == "TABULAR"
        assert DatasetType.CUSTOM.value == "CUSTOM"

    def test_dataset_type_is_enum(self) -> None:
        """验证是 Enum 类型。"""
        from src.modules.datasets.domain.value_objects import DatasetType

        assert issubclass(DatasetType, Enum)

    def test_dataset_type_count(self) -> None:
        """验证枚举值数量。"""
        from src.modules.datasets.domain.value_objects import DatasetType

        assert len(DatasetType) == 6


class TestDatasetVisibility:
    """测试 DatasetVisibility 枚举。"""

    def test_visibility_values(self) -> None:
        """验证可见性枚举值。"""
        from src.modules.datasets.domain.value_objects import DatasetVisibility

        assert DatasetVisibility.PUBLIC.value == "PUBLIC"
        assert DatasetVisibility.PRIVATE.value == "PRIVATE"
        assert DatasetVisibility.RESTRICTED.value == "RESTRICTED"

    def test_visibility_is_enum(self) -> None:
        """验证是 Enum 类型。"""
        from src.modules.datasets.domain.value_objects import DatasetVisibility

        assert issubclass(DatasetVisibility, Enum)

    def test_visibility_count(self) -> None:
        """验证枚举值数量。"""
        from src.modules.datasets.domain.value_objects import DatasetVisibility

        assert len(DatasetVisibility) == 3


class TestDatasetStatus:
    """测试 DatasetStatus 枚举。"""

    def test_status_values(self) -> None:
        """验证状态枚举值。"""
        from src.modules.datasets.domain.value_objects import DatasetStatus

        assert DatasetStatus.AVAILABLE.value == "AVAILABLE"
        assert DatasetStatus.PREPARING.value == "PREPARING"
        assert DatasetStatus.ARCHIVED.value == "ARCHIVED"
        assert DatasetStatus.ERROR.value == "ERROR"

    def test_status_is_enum(self) -> None:
        """验证是 Enum 类型。"""
        from src.modules.datasets.domain.value_objects import DatasetStatus

        assert issubclass(DatasetStatus, Enum)

    def test_status_count(self) -> None:
        """验证枚举值数量。"""
        from src.modules.datasets.domain.value_objects import DatasetStatus

        assert len(DatasetStatus) == 4


class TestDatasetStatusTransitions:
    """测试 DatasetStatus 状态转换规则。"""

    def test_valid_transitions_defined(self) -> None:
        """验证状态转换规则已定义。"""
        from src.modules.datasets.domain.value_objects import DATASET_STATUS_TRANSITIONS, DatasetStatus

        assert isinstance(DATASET_STATUS_TRANSITIONS, dict)
        # 每个状态都应该有转换规则
        for status in DatasetStatus:
            assert status in DATASET_STATUS_TRANSITIONS

    def test_preparing_transitions(self) -> None:
        """验证 PREPARING 状态的转换。"""
        from src.modules.datasets.domain.value_objects import DATASET_STATUS_TRANSITIONS, DatasetStatus

        transitions = DATASET_STATUS_TRANSITIONS[DatasetStatus.PREPARING]
        assert DatasetStatus.AVAILABLE in transitions
        assert DatasetStatus.ERROR in transitions

    def test_available_transitions(self) -> None:
        """验证 AVAILABLE 状态的转换。"""
        from src.modules.datasets.domain.value_objects import DATASET_STATUS_TRANSITIONS, DatasetStatus

        transitions = DATASET_STATUS_TRANSITIONS[DatasetStatus.AVAILABLE]
        assert DatasetStatus.ARCHIVED in transitions
        assert DatasetStatus.PREPARING in transitions  # 允许重新准备

    def test_archived_transitions(self) -> None:
        """验证 ARCHIVED 状态的转换。"""
        from src.modules.datasets.domain.value_objects import DATASET_STATUS_TRANSITIONS, DatasetStatus

        transitions = DATASET_STATUS_TRANSITIONS[DatasetStatus.ARCHIVED]
        assert DatasetStatus.AVAILABLE in transitions  # 可以恢复

    def test_error_transitions(self) -> None:
        """验证 ERROR 状态的转换。"""
        from src.modules.datasets.domain.value_objects import DATASET_STATUS_TRANSITIONS, DatasetStatus

        transitions = DATASET_STATUS_TRANSITIONS[DatasetStatus.ERROR]
        assert DatasetStatus.PREPARING in transitions  # 可以重试
