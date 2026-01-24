"""Checkpoint related enums."""

from enum import Enum


class CheckpointType(Enum):
    """Checkpoint type (matches database checkpointtype enum)."""

    EPOCH = "EPOCH"
    STEP = "STEP"
    BEST = "BEST"
    FINAL = "FINAL"
    MANUAL = "MANUAL"


class StorageTier(Enum):
    """Storage tier for tiered storage (NVMe -> FSx -> S3)."""

    NVME = "NVME"
    FSX = "FSX"
    S3 = "S3"


class CheckpointStatus(Enum):
    """Checkpoint status."""

    AVAILABLE = "AVAILABLE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class CheckpointTriggerType(Enum):
    """Checkpoint trigger type - defines the 5 scenarios that trigger checkpoint creation.

    - SCHEDULED: 定期自动创建检查点 (按配置的 checkpoint_interval)
    - INTERRUPT: 训练中断时创建检查点
    - NODE_FAILURE: 节点故障时创建检查点 (PodsReady=False 持续 >30s)
    - PREEMPTION: 资源抢占时创建检查点 (5分钟超时)
    - MANUAL: 用户手动触发创建检查点
    """

    SCHEDULED = "SCHEDULED"
    INTERRUPT = "INTERRUPT"
    NODE_FAILURE = "NODE_FAILURE"
    PREEMPTION = "PREEMPTION"
    MANUAL = "MANUAL"


# Storage tier migration hierarchy (one-way only: hot -> cold)
STORAGE_TIER_HIERARCHY = {
    StorageTier.NVME: [StorageTier.FSX, StorageTier.S3],
    StorageTier.FSX: [StorageTier.S3],
    StorageTier.S3: [],  # Final tier
}
