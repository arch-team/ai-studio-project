"""Model ORM model - Trained model metadata storage."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.models.base import TimestampMixin
from src.modules.models.domain.value_objects import ModelFramework, ModelStatus

if TYPE_CHECKING:
    from src.modules.training.infrastructure.models import CheckpointModel, TrainingJobModel
    from src.modules.auth.infrastructure.models import UserModel


class ModelModel(Base, TimestampMixin):
    """Model ORM model."""

    __tablename__ = "models"

    # Primary key
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="模型ID",
    )

    # Model identification
    model_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="模型名称",
    )
    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="v1",
        server_default="v1",
        comment="模型版本",
    )
    display_name: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="显示名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="模型描述",
    )

    # Associated training job and checkpoint
    training_job_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("training_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联训练任务ID",
    )
    checkpoint_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("checkpoints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联检查点ID",
    )

    # Owner
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所有者用户ID",
    )

    # Storage location
    model_uri: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="模型存储路径 (S3 URI)",
    )

    # SageMaker Model Registry integration
    registry_arn: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        index=True,
        comment="SageMaker Model Registry ARN",
    )
    registry_status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="Registry 同步状态",
    )

    # Model metrics (training results)
    metrics: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="模型指标 (JSON: accuracy, loss, f1_score 等)",
    )

    # Hyperparameters used for training
    hyperparameters: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="训练超参数 (JSON)",
    )

    # Model framework
    framework: Mapped[ModelFramework] = mapped_column(
        Enum(ModelFramework),
        nullable=False,
        default=ModelFramework.PYTORCH,
        server_default="PYTORCH",
        index=True,
        comment="模型框架",
    )
    framework_version: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="框架版本 (例如: 2.1.0)",
    )

    # Model status
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus),
        nullable=False,
        default=ModelStatus.TRAINING,
        server_default="TRAINING",
        index=True,
        comment="模型状态",
    )

    # Model size and format
    size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="模型大小 (字节)",
    )
    model_format: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="模型格式 (例如: safetensors, pickle, onnx)",
    )

    # Tags for organization
    tags: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="标签 (JSON 数组)",
    )

    # Registration and archive timestamps
    registered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="注册到 Registry 的时间",
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="归档时间",
    )

    # Relationships
    training_job: Mapped[Optional["TrainingJobModel"]] = relationship(
        "TrainingJobModel",
        back_populates="models",
    )
    checkpoint: Mapped[Optional["CheckpointModel"]] = relationship(
        "CheckpointModel",
        back_populates="models",
    )
    owner: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="models",
    )

    __table_args__ = ({"comment": "模型表"},)

    def is_training(self) -> bool:
        """Check if model is currently training."""
        return self.status == ModelStatus.TRAINING

    def is_registered(self) -> bool:
        """Check if model is registered."""
        return self.status == ModelStatus.REGISTERED

    def is_deployed(self) -> bool:
        """Check if model is deployed."""
        return self.status == ModelStatus.DEPLOYED

    def is_archived(self) -> bool:
        """Check if model is archived."""
        return self.status == ModelStatus.ARCHIVED
