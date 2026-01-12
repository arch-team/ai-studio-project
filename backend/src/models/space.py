"""Space model - SQLAlchemy 2.0 async model.

Task: T011c - 创建 Space 模型
支持 SageMaker Studio Spaces 集成 (JupyterLab/VSCode),
包含实例类型、空间类型、软删除等功能
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CHAR, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class SpaceInstanceType(str, PyEnum):
    """Space 实例类型枚举 (基于 SageMaker 支持的实例类型)."""

    ML_T3_MEDIUM = "ml.t3.medium"
    ML_T3_LARGE = "ml.t3.large"
    ML_G4DN_XLARGE = "ml.g4dn.xlarge"
    ML_G5_XLARGE = "ml.g5.xlarge"
    ML_G5_2XLARGE = "ml.g5.2xlarge"


class SpaceType(str, PyEnum):
    """Space 类型枚举."""

    JUPYTER = "jupyter"
    VSCODE = "vscode"
    RSTUDIO = "rstudio"


class SpaceStatus(str, PyEnum):
    """Space 状态枚举 (对应 SageMaker Space 状态)."""

    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DELETED = "deleted"


class Space(Base):
    """开发空间模型 - 支持 SageMaker Studio Spaces 集成."""

    __tablename__ = "development_spaces"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
        "comment": "开发空间表",
    }

    # 主键 (UUID)
    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Space ID (UUID)",
    )

    # Space 标识
    space_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Space 名称",
    )

    # 所有者
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所有者用户ID (UUID)",
    )

    # 实例配置
    instance_type: Mapped[SpaceInstanceType] = mapped_column(
        Enum(SpaceInstanceType, name="space_instance_type"),
        nullable=False,
        default=SpaceInstanceType.ML_G5_XLARGE,
        comment="实例类型",
    )

    # Space 类型
    space_type: Mapped[SpaceType] = mapped_column(
        Enum(SpaceType, name="space_type"),
        nullable=False,
        default=SpaceType.JUPYTER,
        comment="Space 类型",
    )

    # Space 状态
    status: Mapped[SpaceStatus] = mapped_column(
        Enum(SpaceStatus, name="space_status"),
        nullable=False,
        default=SpaceStatus.PENDING,
        comment="Space 状态",
    )

    # 存储配置
    storage_size_gb: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=50,
        comment="存储大小 (GB)",
    )

    # SageMaker 集成
    lifecycle_config_arn: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Lifecycle 配置 ARN",
    )
    sagemaker_space_arn: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="SageMaker Space ARN",
    )
    studio_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        comment="SageMaker Studio URL",
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
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间 (软删除)",
    )

    # 关联关系
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="spaces",
        foreign_keys=[owner_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Space(id={self.id}, name='{self.space_name}', status={self.status.value})>"

    @property
    def is_deleted(self) -> bool:
        """Check if space is soft deleted."""
        return self.deleted_at is not None

    @property
    def is_running(self) -> bool:
        """Check if space is currently running."""
        return self.status == SpaceStatus.RUNNING and not self.is_deleted

    @property
    def can_start(self) -> bool:
        """Check if space can be started."""
        return self.status in (SpaceStatus.STOPPED, SpaceStatus.PENDING) and not self.is_deleted

    @property
    def can_stop(self) -> bool:
        """Check if space can be stopped."""
        return self.status == SpaceStatus.RUNNING and not self.is_deleted

    def soft_delete(self) -> None:
        """Perform soft delete by setting deleted_at timestamp."""
        self.deleted_at = datetime.utcnow()
        self.status = SpaceStatus.DELETED
