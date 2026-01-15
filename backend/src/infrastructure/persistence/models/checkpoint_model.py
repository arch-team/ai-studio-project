"""Checkpoint ORM model - Training checkpoint metadata storage."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.domain.entities.checkpoint import (
    CheckpointStatus,
    CheckpointType,
    StorageTier,
)
from src.infrastructure.persistence.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.persistence.models.ml_model import ModelModel
    from src.infrastructure.persistence.models.training_job_model import TrainingJobModel


class CheckpointModel(Base, TimestampMixin):
    """Checkpoint ORM model."""

    __tablename__ = "checkpoints"

    # Primary key
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="检查点ID",
    )

    # Associated training job
    training_job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("training_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联训练任务ID",
    )

    # Checkpoint identification
    checkpoint_name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="检查点名称 (例如: checkpoint-epoch100.pth)",
    )
    storage_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="存储路径 (例如: /fsx/checkpoints/job-123/checkpoint-epoch100.pth)",
    )

    # Checkpoint type
    checkpoint_type: Mapped[CheckpointType] = mapped_column(
        Enum(CheckpointType),
        nullable=False,
        default=CheckpointType.EPOCH,
        server_default="EPOCH",
        comment="检查点类型",
    )

    # Training progress
    epoch: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="训练轮次",
    )
    step: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="训练步数",
    )

    # Checkpoint statistics
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="文件大小 (字节)",
    )

    # Checksum for integrity verification
    checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 校验和",
    )

    # Training metrics at checkpoint save time
    loss: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=10, scale=6),
        nullable=True,
        comment="损失值",
    )
    accuracy: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=5, scale=4),
        nullable=True,
        comment="准确率",
    )
    metrics: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="其他指标 (JSON 对象)",
    )

    # Storage tier (tiered storage: NVMe -> FSx -> S3)
    storage_tier: Mapped[StorageTier] = mapped_column(
        Enum(StorageTier),
        nullable=False,
        default=StorageTier.FSX,
        server_default="FSX",
        index=True,
        comment="存储层级",
    )

    # Checkpoint status
    status: Mapped[CheckpointStatus] = mapped_column(
        Enum(CheckpointStatus),
        nullable=False,
        default=CheckpointStatus.AVAILABLE,
        server_default="AVAILABLE",
        index=True,
        comment="检查点状态",
    )

    # Archive/delete timestamps
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="归档时间 (S3)",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="删除时间 (软删除)",
    )

    # Relationships
    training_job: Mapped["TrainingJobModel"] = relationship(
        "TrainingJobModel",
        back_populates="checkpoints",
    )
    models: Mapped[list["ModelModel"]] = relationship(
        "ModelModel",
        back_populates="checkpoint",
    )

    __table_args__ = ({"comment": "检查点表"},)

    def is_available(self) -> bool:
        """Check if checkpoint is available."""
        return self.status == CheckpointStatus.AVAILABLE

    def is_archived(self) -> bool:
        """Check if checkpoint is archived."""
        return self.status == CheckpointStatus.ARCHIVED

    def is_deleted(self) -> bool:
        """Check if checkpoint is deleted."""
        return self.status == CheckpointStatus.DELETED
