"""ResourceLimitConfig ORM model - Per-job resource limits by role."""

import enum
from typing import Optional

from sqlalchemy import BigInteger, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.infrastructure.persistence.models.base import TimestampMixin


class LimitRole(enum.Enum):
    """Role for resource limit configuration."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class PriorityDefault(enum.Enum):
    """Default priority for training jobs."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResourceLimitConfigModel(Base, TimestampMixin):
    """Resource limit configuration ORM model."""

    __tablename__ = "resource_limit_configs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="配置ID",
    )

    # Configuration identification
    config_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="配置名称",
    )

    # Role association
    role: Mapped[LimitRole] = mapped_column(
        Enum(LimitRole),
        nullable=False,
        index=True,
        comment="适用角色",
    )

    # Project scope (nullable for global config)
    project_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="项目ID(空表示全局配置)",
    )

    # Per-job resource limits
    max_gpu_per_job: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=8,
        comment="单任务最大GPU数",
    )
    max_cpu_per_job: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=64,
        comment="单任务最大CPU核心数",
    )
    max_memory_gb_per_job: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=512,
        comment="单任务最大内存(GB)",
    )
    max_storage_gb_per_job: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        comment="单任务最大存储(GB)",
    )
    max_nodes_per_job: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4,
        comment="单任务最大节点数",
    )

    # Default priority
    priority_default: Mapped[PriorityDefault] = mapped_column(
        Enum(PriorityDefault),
        nullable=False,
        default=PriorityDefault.MEDIUM,
        comment="默认优先级",
    )

    __table_args__ = ({"comment": "资源限制配置表"},)
