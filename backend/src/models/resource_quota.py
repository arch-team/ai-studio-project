"""ResourceQuota model - SQLAlchemy 2.0 async model.

Task: T012 - 创建 SQLAlchemy ResourceQuota 模型
包含配额验证逻辑,支持 Kueue ClusterQueue 和 ResourceFlavor 映射
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class QuotaType(str, PyEnum):
    """配额类型枚举."""

    USER = "user"
    TEAM = "team"
    PROJECT = "project"


class QuotaStatus(str, PyEnum):
    """配额状态枚举."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class ResourceQuota(Base):
    """资源配额模型 - 定义用户或组的资源配额限制,支持多租户资源管理 (基于 Kueue)."""

    __tablename__ = "resource_quotas"
    __table_args__ = (
        UniqueConstraint("name", name="uk_resource_quotas_name"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
            "comment": "资源配额表",
        },
    )

    # 主键
    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="配额ID",
    )

    # 配额标识
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="配额名称 (例如: team-a-quota)",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="配额描述",
    )

    # 配额类型
    quota_type: Mapped[QuotaType] = mapped_column(
        Enum(QuotaType, name="quota_type"),
        nullable=False,
        default=QuotaType.USER,
        comment="配额类型",
    )

    # CPU 配额 (单位: vCPU)
    max_cpu_cores: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        comment="最大 CPU 核心数",
    )
    reserved_cpu_cores: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        comment="预留 CPU 核心数",
    )

    # GPU 配额
    max_gpu_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        comment="最大 GPU 数量",
    )
    reserved_gpu_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        comment="预留 GPU 数量",
    )
    gpu_types: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment='允许的 GPU 类型 (例如: ["ml.p4d.24xlarge", "ml.g5.xlarge"])',
    )

    # 内存配额 (单位: GB)
    max_memory_gb: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        comment="最大内存 (GB)",
    )
    reserved_memory_gb: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        comment="预留内存 (GB)",
    )

    # 存储配额 (单位: GB)
    max_storage_gb: Mapped[Optional[int]] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
        comment="最大存储空间 (GB)",
    )

    # 训练任务配额
    max_concurrent_jobs: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=5,
        comment="最大并发训练任务数",
    )
    max_total_jobs: Mapped[Optional[int]] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
        comment="总训练任务数限制 (NULL 表示无限制)",
    )

    # Spot 实例配额
    max_spot_instances: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        comment="最大 Spot 实例数",
    )

    # 配额状态
    status: Mapped[QuotaStatus] = mapped_column(
        Enum(QuotaStatus, name="quota_status"),
        nullable=False,
        default=QuotaStatus.ACTIVE,
        comment="配额状态",
    )

    # 有效期
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="生效时间",
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="过期时间 (NULL 表示永久)",
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
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建人用户ID (UUID)",
    )

    # 关联关系
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="resource_quota",
        foreign_keys="User.resource_quota_id",
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ResourceQuota(id={self.id}, name='{self.name}', type={self.quota_type.value})>"

    @property
    def is_active(self) -> bool:
        """Check if quota is currently active and valid."""
        if self.status != QuotaStatus.ACTIVE:
            return False
        now = datetime.utcnow()
        if self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        return True

    @property
    def available_cpu_cores(self) -> int:
        """Get available (non-reserved) CPU cores."""
        return self.max_cpu_cores - self.reserved_cpu_cores

    @property
    def available_gpu_count(self) -> int:
        """Get available (non-reserved) GPU count."""
        return self.max_gpu_count - self.reserved_gpu_count

    @property
    def available_memory_gb(self) -> int:
        """Get available (non-reserved) memory in GB."""
        return self.max_memory_gb - self.reserved_memory_gb

    def can_allocate(
        self,
        cpu_cores: int = 0,
        gpu_count: int = 0,
        memory_gb: int = 0,
        storage_gb: int = 0,
    ) -> bool:
        """Check if resources can be allocated within quota limits.

        Args:
            cpu_cores: Required CPU cores
            gpu_count: Required GPU count
            memory_gb: Required memory in GB
            storage_gb: Required storage in GB

        Returns:
            True if allocation is possible
        """
        if not self.is_active:
            return False
        if cpu_cores > self.available_cpu_cores:
            return False
        if gpu_count > self.available_gpu_count:
            return False
        if memory_gb > self.available_memory_gb:
            return False
        if self.max_storage_gb and storage_gb > self.max_storage_gb:
            return False
        return True

    def is_gpu_type_allowed(self, gpu_type: str) -> bool:
        """Check if a specific GPU type is allowed.

        Args:
            gpu_type: The GPU instance type to check

        Returns:
            True if GPU type is allowed (or if no restrictions are set)
        """
        if not self.gpu_types:
            return True  # No restrictions
        return gpu_type in self.gpu_types
