"""Checkpoint ORM model - Training checkpoint metadata storage."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.models import TimestampMixin
from src.modules.training.domain.value_objects import (
    CheckpointStatus,
    CheckpointTriggerType,
    CheckpointType,
    StorageTier,
)

if TYPE_CHECKING:
    from .training_job_model import TrainingJobModel
    from src.modules.models.infrastructure.models import ModelModel


class CheckpointModel(Base, TimestampMixin):
    """Checkpoint ORM model."""

    __tablename__ = "checkpoints"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="检查点ID")

    # Associated training job
    training_job_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("training_jobs.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联训练任务ID")

    # Checkpoint identification
    checkpoint_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="检查点名称")
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False, comment="存储路径")

    # Checkpoint type and trigger
    checkpoint_type: Mapped[CheckpointType] = mapped_column(Enum(CheckpointType), nullable=False, default=CheckpointType.EPOCH, comment="检查点类型")
    trigger_type: Mapped[CheckpointTriggerType] = mapped_column(Enum(CheckpointTriggerType), nullable=False, default=CheckpointTriggerType.SCHEDULED, comment="触发类型")

    # Training progress
    epoch: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, comment="训练轮次")
    step: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="训练步数")

    # Checkpoint statistics
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="文件大小(字节)")
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="SHA-256校验和")

    # Training metrics at checkpoint save time
    loss: Mapped[Decimal | None] = mapped_column(DECIMAL(precision=10, scale=6), nullable=True, comment="损失值")
    accuracy: Mapped[Decimal | None] = mapped_column(DECIMAL(precision=5, scale=4), nullable=True, comment="准确率")
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="其他指标")

    # Storage tier
    storage_tier: Mapped[StorageTier] = mapped_column(Enum(StorageTier), nullable=False, default=StorageTier.FSX, index=True, comment="存储层级")
    status: Mapped[CheckpointStatus] = mapped_column(Enum(CheckpointStatus), nullable=False, default=CheckpointStatus.AVAILABLE, index=True, comment="检查点状态")

    # Archive/delete timestamps
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True, comment="归档时间")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True, comment="删除时间")

    # Relationships
    training_job: Mapped["TrainingJobModel"] = relationship("TrainingJobModel", back_populates="checkpoints", foreign_keys=[training_job_id])
    models: Mapped[list["ModelModel"]] = relationship("ModelModel", back_populates="checkpoint")

    __table_args__ = ({"comment": "检查点表"},)
