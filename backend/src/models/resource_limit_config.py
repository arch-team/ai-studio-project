"""ResourceLimitConfig model - SQLAlchemy 2.0 async model.

Task: T012b - 创建 ResourceLimitConfig 模型
包含限制验证逻辑,关联 User (通过 role),支持项目级和全局级配置
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Enum, String, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class LimitConfigRole(str, PyEnum):
    """资源限制配置角色枚举."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class PriorityLevel(str, PyEnum):
    """任务优先级枚举 (与 Kueue PriorityClass 对应)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResourceLimitConfig(Base):
    """资源限制配置模型 - 定义基于角色的单任务资源限制."""

    __tablename__ = "resource_limit_configs"
    __table_args__ = (
        UniqueConstraint("role", "project_id", name="uk_resource_limit_configs_role_project"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
            "comment": "资源限制配置表",
        },
    )

    # 主键
    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="配置ID",
    )

    # 配置标识
    config_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="配置名称",
    )

    # 角色限制 (基于用户角色)
    role: Mapped[LimitConfigRole] = mapped_column(
        Enum(LimitConfigRole, name="limit_config_role"),
        nullable=False,
        comment="适用角色",
    )

    # 项目关联 (NULL 表示全局配置)
    project_id: Mapped[Optional[int]] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
        comment="项目ID (NULL 表示全局配置)",
    )

    # 单任务资源限制
    max_gpu_per_job: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=8,
        comment="单任务最大 GPU 数量",
    )
    max_cpu_per_job: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=64,
        comment="单任务最大 CPU 核心数",
    )
    max_memory_gb_per_job: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=512,
        comment="单任务最大内存 (GB)",
    )
    max_storage_gb_per_job: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=1000,
        comment="单任务最大存储 (GB)",
    )
    max_nodes_per_job: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=4,
        comment="单任务最大节点数",
    )

    # 默认优先级
    priority_default: Mapped[PriorityLevel] = mapped_column(
        Enum(PriorityLevel, name="priority_level"),
        nullable=False,
        default=PriorityLevel.MEDIUM,
        comment="默认任务优先级",
    )

    # 审计字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    def __repr__(self) -> str:
        """String representation."""
        project_info = f", project_id={self.project_id}" if self.project_id else ", global"
        return f"<ResourceLimitConfig(id={self.id}, role={self.role.value}{project_info})>"

    @property
    def is_global(self) -> bool:
        """Check if this is a global configuration (not project-specific)."""
        return self.project_id is None

    def validate_job_resources(
        self,
        gpu_count: int = 0,
        cpu_cores: int = 0,
        memory_gb: int = 0,
        storage_gb: int = 0,
        node_count: int = 1,
    ) -> tuple[bool, Optional[str]]:
        """Validate if job resources are within limits.

        Args:
            gpu_count: Requested GPU count
            cpu_cores: Requested CPU cores
            memory_gb: Requested memory in GB
            storage_gb: Requested storage in GB
            node_count: Requested node count

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

    @classmethod
    def get_default_limits(cls, role: LimitConfigRole) -> dict:
        """Get default resource limits for a role.

        Args:
            role: The user role

        Returns:
            Dictionary of default limits
        """
        defaults = {
            LimitConfigRole.ADMIN: {
                "max_gpu_per_job": 64,
                "max_cpu_per_job": 512,
                "max_memory_gb_per_job": 2048,
                "max_storage_gb_per_job": 10000,
                "max_nodes_per_job": 16,
                "priority_default": PriorityLevel.HIGH,
            },
            LimitConfigRole.PROJECT_MANAGER: {
                "max_gpu_per_job": 32,
                "max_cpu_per_job": 256,
                "max_memory_gb_per_job": 1024,
                "max_storage_gb_per_job": 5000,
                "max_nodes_per_job": 8,
                "priority_default": PriorityLevel.MEDIUM,
            },
            LimitConfigRole.ENGINEER: {
                "max_gpu_per_job": 8,
                "max_cpu_per_job": 64,
                "max_memory_gb_per_job": 512,
                "max_storage_gb_per_job": 1000,
                "max_nodes_per_job": 4,
                "priority_default": PriorityLevel.MEDIUM,
            },
            LimitConfigRole.VIEWER: {
                "max_gpu_per_job": 0,
                "max_cpu_per_job": 0,
                "max_memory_gb_per_job": 0,
                "max_storage_gb_per_job": 0,
                "max_nodes_per_job": 0,
                "priority_default": PriorityLevel.LOW,
            },
        }
        return defaults.get(role, defaults[LimitConfigRole.ENGINEER])
