"""Dataset 领域实体 - 数据集管理核心业务对象。"""

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.utils import utc_now

from ..value_objects import (
    DATASET_STATUS_TRANSITIONS,
    DatasetStatus,
    DatasetStorageType,
    DatasetType,
    DatasetVisibility,
)


@dataclass
class Dataset:
    """数据集领域实体。"""

    # === 必填字段 ===
    id: int
    name: str
    storage_type: DatasetStorageType
    storage_uri: str
    dataset_type: DatasetType
    owner_id: int

    # === 可选标识字段 ===
    description: str | None = None
    version: str = "v1"

    # === 数据统计字段 ===
    total_size_bytes: int | None = None
    file_count: int | None = None

    # === 数据格式字段 ===
    data_format: str | None = None
    tags: list[str] | None = None

    # === 访问控制 ===
    visibility: DatasetVisibility = DatasetVisibility.PRIVATE
    status: DatasetStatus = DatasetStatus.PREPARING

    # === 时间戳 ===
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    last_accessed_at: datetime | None = None

    # === 状态转换方法 ===

    def can_transition_to(self, new_status: DatasetStatus) -> bool:
        """检查是否可以转换到目标状态。"""
        valid_transitions = DATASET_STATUS_TRANSITIONS.get(self.status, set())
        return new_status in valid_transitions

    def transition_to(self, new_status: DatasetStatus) -> None:
        """转换到新状态，无效转换抛出 InvalidStateTransitionError。"""
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                "Dataset", self.status.value, new_status.value
            )

        self.status = new_status
        self.updated_at = utc_now()

    # === 便捷状态转换方法 ===

    def mark_available(self) -> None:
        """标记数据集为可用状态。"""
        self.transition_to(DatasetStatus.AVAILABLE)

    def mark_error(self) -> None:
        """标记数据集为错误状态。"""
        self.transition_to(DatasetStatus.ERROR)

    def archive(self) -> None:
        """归档数据集。"""
        self.transition_to(DatasetStatus.ARCHIVED)

    def restore(self) -> None:
        """从归档状态恢复数据集。"""
        self.transition_to(DatasetStatus.AVAILABLE)

    # === 状态查询方法 ===

    def is_available(self) -> bool:
        """检查数据集是否可用。"""
        return self.status == DatasetStatus.AVAILABLE

    def is_archived(self) -> bool:
        """检查数据集是否已归档。"""
        return self.status == DatasetStatus.ARCHIVED

    def has_error(self) -> bool:
        """检查数据集是否处于错误状态。"""
        return self.status == DatasetStatus.ERROR

    # === 访问控制方法 ===

    def is_public(self) -> bool:
        """检查数据集是否公开。"""
        return self.visibility == DatasetVisibility.PUBLIC

    def is_accessible_by(self, user_id: int) -> bool:
        """检查指定用户是否可以访问此数据集。"""
        # 所有者始终可以访问
        if user_id == self.owner_id:
            return True

        # 公开数据集所有人可访问
        if self.is_public():
            return True

        # RESTRICTED 类型需要额外权限检查（此处简化处理）
        # 私有数据集只有所有者可访问
        return False

    # === 实用方法 ===

    def update_access_time(self) -> None:
        """更新最后访问时间。"""
        self.last_accessed_at = utc_now()
        self.updated_at = utc_now()
