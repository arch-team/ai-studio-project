"""Space value objects - Enums for space configuration and status."""

from enum import Enum


class SpaceInstanceType(Enum):
    """Space instance type options."""

    ML_T3_MEDIUM = "ml.t3.medium"
    ML_T3_LARGE = "ml.t3.large"
    ML_G4DN_XLARGE = "ml.g4dn.xlarge"
    ML_G5_XLARGE = "ml.g5.xlarge"
    ML_G5_2XLARGE = "ml.g5.2xlarge"


class SpaceType(Enum):
    """Space IDE type."""

    JUPYTER = "jupyter"
    VSCODE = "vscode"
    RSTUDIO = "rstudio"


class SpaceStatus(Enum):
    """Space lifecycle status."""

    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DELETED = "deleted"


# Valid state transitions
SPACE_STATE_TRANSITIONS = {
    SpaceStatus.PENDING: {SpaceStatus.RUNNING, SpaceStatus.FAILED},
    SpaceStatus.RUNNING: {SpaceStatus.STOPPED, SpaceStatus.FAILED},
    SpaceStatus.STOPPED: {SpaceStatus.RUNNING, SpaceStatus.FAILED, SpaceStatus.DELETED},
    SpaceStatus.FAILED: {SpaceStatus.PENDING, SpaceStatus.DELETED},
    SpaceStatus.DELETED: set(),  # Terminal state
}


# Resource map for instance types
INSTANCE_TYPE_RESOURCES = {
    SpaceInstanceType.ML_T3_MEDIUM: {
        "cpu_cores": 2,
        "memory_gb": 4,
        "gpu_count": 0,
    },
    SpaceInstanceType.ML_T3_LARGE: {
        "cpu_cores": 2,
        "memory_gb": 8,
        "gpu_count": 0,
    },
    SpaceInstanceType.ML_G4DN_XLARGE: {
        "cpu_cores": 4,
        "memory_gb": 16,
        "gpu_count": 1,
    },
    SpaceInstanceType.ML_G5_XLARGE: {
        "cpu_cores": 4,
        "memory_gb": 16,
        "gpu_count": 1,
    },
    SpaceInstanceType.ML_G5_2XLARGE: {
        "cpu_cores": 8,
        "memory_gb": 32,
        "gpu_count": 1,
    },
}
