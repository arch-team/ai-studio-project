"""Dataset 值对象枚举定义。"""

from enum import Enum


class DatasetStorageType(Enum):
    """数据集存储类型 (对应 data-model.md storage_type 枚举)。"""

    FSX = "FSX"
    S3 = "S3"
    EFS = "EFS"


class DatasetType(Enum):
    """数据集类型 (对应 data-model.md dataset_type 枚举)。"""

    IMAGE = "IMAGE"
    TEXT = "TEXT"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    TABULAR = "TABULAR"
    CUSTOM = "CUSTOM"


class DatasetVisibility(Enum):
    """数据集可见性 (对应 data-model.md visibility 枚举)。"""

    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class DatasetStatus(Enum):
    """数据集状态 (对应 data-model.md status 枚举)。"""

    AVAILABLE = "AVAILABLE"
    PREPARING = "PREPARING"
    ARCHIVED = "ARCHIVED"
    ERROR = "ERROR"


# 状态转换规则 - 定义从各状态允许转换到的目标状态
DATASET_STATUS_TRANSITIONS: dict[DatasetStatus, set[DatasetStatus]] = {
    # PREPARING: 可以变为可用或错误
    DatasetStatus.PREPARING: {DatasetStatus.AVAILABLE, DatasetStatus.ERROR},
    # AVAILABLE: 可以归档或重新准备
    DatasetStatus.AVAILABLE: {DatasetStatus.ARCHIVED, DatasetStatus.PREPARING},
    # ARCHIVED: 可以恢复为可用
    DatasetStatus.ARCHIVED: {DatasetStatus.AVAILABLE},
    # ERROR: 可以重试准备
    DatasetStatus.ERROR: {DatasetStatus.PREPARING},
}
