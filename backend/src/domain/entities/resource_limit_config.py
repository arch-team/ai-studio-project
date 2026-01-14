"""ResourceLimitConfig domain entity - Per-job resource limits by role."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class LimitRole(Enum):
    """Role for resource limit configuration."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class PriorityDefault(Enum):
    """Default priority levels for training jobs."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def to_kueue_priority(self) -> int:
        """Convert to Kueue priority class value."""
        mapping = {
            PriorityDefault.HIGH: 1000,
            PriorityDefault.MEDIUM: 500,
            PriorityDefault.LOW: 100,
        }
        return mapping[self]


@dataclass
class ResourceLimitConfig:
    """Resource limit configuration per role and optionally per project.

    Defines maximum resource limits per job for different user roles.
    Global configs (project_id=None) apply as defaults.
    Project-specific configs override global configs.
    """

    id: int
    config_name: str
    role: LimitRole

    # Project scope (None = global config)
    project_id: Optional[int] = None

    # Per-job limits
    max_gpu_per_job: int = 8
    max_cpu_per_job: int = 96
    max_memory_gb_per_job: int = 768
    max_storage_gb_per_job: int = 1000
    max_nodes_per_job: int = 8

    # Default priority
    priority_default: PriorityDefault = PriorityDefault.MEDIUM

    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def is_global_config(self) -> bool:
        """Check if this is a global (not project-specific) config."""
        return self.project_id is None

    def validate_job_resources(
        self,
        gpu_count: int,
        cpu_cores: int,
        memory_gb: int,
        storage_gb: int,
        node_count: int,
    ) -> tuple[bool, Optional[str]]:
        """Validate job resources against limits.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if gpu_count > self.max_gpu_per_job:
            return False, f"GPU count {gpu_count} exceeds limit {self.max_gpu_per_job}"

        if cpu_cores > self.max_cpu_per_job:
            return False, f"CPU cores {cpu_cores} exceeds limit {self.max_cpu_per_job}"

        if memory_gb > self.max_memory_gb_per_job:
            return False, f"Memory {memory_gb}GB exceeds limit {self.max_memory_gb_per_job}GB"

        if storage_gb > self.max_storage_gb_per_job:
            return False, f"Storage {storage_gb}GB exceeds limit {self.max_storage_gb_per_job}GB"

        if node_count > self.max_nodes_per_job:
            return False, f"Node count {node_count} exceeds limit {self.max_nodes_per_job}"

        return True, None

    def get_default_priority_value(self) -> int:
        """Get default Kueue priority value for this config."""
        return self.priority_default.to_kueue_priority()

    @staticmethod
    def get_default_for_role(role: LimitRole) -> "ResourceLimitConfig":
        """Get default resource limits for a given role.

        Factory method returning sensible defaults based on role hierarchy.
        """
        defaults = {
            LimitRole.ADMIN: {
                "max_gpu_per_job": 64,
                "max_cpu_per_job": 768,
                "max_memory_gb_per_job": 6144,
                "max_storage_gb_per_job": 10000,
                "max_nodes_per_job": 64,
                "priority_default": PriorityDefault.HIGH,
            },
            LimitRole.PROJECT_MANAGER: {
                "max_gpu_per_job": 32,
                "max_cpu_per_job": 384,
                "max_memory_gb_per_job": 3072,
                "max_storage_gb_per_job": 5000,
                "max_nodes_per_job": 32,
                "priority_default": PriorityDefault.MEDIUM,
            },
            LimitRole.ENGINEER: {
                "max_gpu_per_job": 8,
                "max_cpu_per_job": 96,
                "max_memory_gb_per_job": 768,
                "max_storage_gb_per_job": 1000,
                "max_nodes_per_job": 8,
                "priority_default": PriorityDefault.MEDIUM,
            },
            LimitRole.VIEWER: {
                "max_gpu_per_job": 0,
                "max_cpu_per_job": 0,
                "max_memory_gb_per_job": 0,
                "max_storage_gb_per_job": 0,
                "max_nodes_per_job": 0,
                "priority_default": PriorityDefault.LOW,
            },
        }

        role_defaults = defaults[role]
        return ResourceLimitConfig(
            id=0,  # Temporary ID for default config
            config_name=f"default_{role.value}",
            role=role,
            **role_defaults,
        )
