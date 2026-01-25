"""训练模块常量定义"""

from typing import Final

# ============================================================================
# 默认配置常量
# ============================================================================

# 计算资源默认值
DEFAULT_NODE_COUNT: Final[int] = 1
DEFAULT_TASKS_PER_NODE: Final[int] = 1
DEFAULT_GPU_PER_NODE: Final[int] = 1

# 存储挂载路径
DEFAULT_DATA_MOUNT_PATH: Final[str] = "/data"
DEFAULT_CHECKPOINT_MOUNT_PATH: Final[str] = "/checkpoints"
DEFAULT_MODEL_MOUNT_PATH: Final[str] = "/models"

# Kubernetes 配置
DEFAULT_NAMESPACE: Final[str] = "default"
DEFAULT_CONTAINER_NAME: Final[str] = "pytorch"

# 资源类型
RESOURCE_TYPE_GPU: Final[str] = "gpu"
RESOURCE_TYPE_CPU: Final[str] = "cpu"
RESOURCE_TYPE_MEMORY: Final[str] = "memory"

# ============================================================================
# GPU 实例类型映射
# ============================================================================

GPU_INSTANCE_MAPPING: Final[dict[str, int]] = {
    # P4 系列 (NVIDIA A100)
    "ml.p4d.24xlarge": 8,
    "ml.p4de.24xlarge": 8,

    # P3 系列 (NVIDIA V100)
    "ml.p3.2xlarge": 1,
    "ml.p3.8xlarge": 4,
    "ml.p3.16xlarge": 8,
    "ml.p3dn.24xlarge": 8,

    # G4 系列 (NVIDIA T4)
    "ml.g4dn.xlarge": 1,
    "ml.g4dn.2xlarge": 1,
    "ml.g4dn.4xlarge": 1,
    "ml.g4dn.8xlarge": 1,
    "ml.g4dn.12xlarge": 4,
    "ml.g4dn.16xlarge": 1,
    "ml.g4dn.metal": 8,

    # G5 系列 (NVIDIA A10G)
    "ml.g5.xlarge": 1,
    "ml.g5.2xlarge": 1,
    "ml.g5.4xlarge": 1,
    "ml.g5.8xlarge": 1,
    "ml.g5.12xlarge": 4,
    "ml.g5.16xlarge": 1,
    "ml.g5.24xlarge": 4,
    "ml.g5.48xlarge": 8,

    # TRN1 系列 (AWS Trainium)
    "ml.trn1.2xlarge": 1,
    "ml.trn1.32xlarge": 16,
    "ml.trn1n.32xlarge": 16,
}

# ============================================================================
# HyperPod/Kubernetes 状态映射
# ============================================================================

HYPERPOD_STATUS_MAPPING: Final[dict[str, str]] = {
    # HyperPod/Kubernetes job condition types
    "Pending": "submitted",
    "Created": "submitted",
    "Scheduled": "submitted",
    "Running": "running",
    "Succeeded": "completed",
    "Completed": "completed",
    "Failed": "failed",
    "Error": "failed",

    # Kueue Task Governance 状态
    "Suspended": "suspended",
    "Preempted": "preempted",
}

# ============================================================================
# 时间相关常量
# ============================================================================

# 检查点间隔（秒）
MIN_CHECKPOINT_INTERVAL: Final[int] = 300  # 5分钟
DEFAULT_CHECKPOINT_INTERVAL: Final[int] = 1800  # 30分钟
MAX_CHECKPOINT_INTERVAL: Final[int] = 7200  # 2小时

# 任务超时（秒）
DEFAULT_JOB_TIMEOUT: Final[int] = 86400  # 24小时
MAX_JOB_TIMEOUT: Final[int] = 604800  # 7天

# 卡住检测阈值（秒）
STALL_DETECTION_THRESHOLD: Final[int] = 3600  # 1小时

# ============================================================================
# 分页相关常量
# ============================================================================

DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100