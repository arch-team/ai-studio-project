"""TrainingJob ORM model - Training task metadata storage."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.training.domain.value_objects import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
    SpotInterruptionBehavior,
)
from src.shared.infrastructure.database import Base
from src.shared.infrastructure.models import TimestampMixin

if TYPE_CHECKING:
    from src.modules.auth.infrastructure.models import UserModel
    from src.modules.models.infrastructure.models import ModelModel

    from .checkpoint_model import CheckpointModel


class TrainingJobModel(Base, TimestampMixin):
    """Training job ORM model."""

    __tablename__ = "training_jobs"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="训练任务ID")

    # Job identification
    job_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True, comment="任务名称")
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="显示名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="任务描述")

    # Owner
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="所有者用户ID"
    )

    # Training configuration
    image_uri: Mapped[str] = mapped_column(String(512), nullable=False, comment="Docker 镜像 URI")
    instance_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="实例类型")
    node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="节点数量")
    tasks_per_node: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="每节点任务数")

    # Commands and environment
    entrypoint_command: Mapped[list] = mapped_column(JSON, nullable=False, comment="启动命令")
    environment_variables: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="环境变量")

    # Dataset and checkpoints
    dataset_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment="关联数据集ID")
    data_mount_path: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="数据挂载路径")
    checkpoint_mount_path: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="检查点挂载路径")
    checkpoint_interval: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="检查点保存间隔")
    auto_resume_checkpoint_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("checkpoints.id", ondelete="SET NULL"), nullable=True, comment="自动恢复检查点ID"
    )

    # Hyperparameters
    hyperparameters: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="超参数")
    max_epochs: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="最大训练轮数")
    batch_size: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="批次大小")
    learning_rate: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=10, scale=8), nullable=True, comment="学习率"
    )

    # Distribution
    distribution_strategy: Mapped[DistributionStrategy] = mapped_column(
        Enum(DistributionStrategy), nullable=False, default=DistributionStrategy.DDP, comment="分布式策略"
    )
    mixed_precision: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="混合精度训练")

    # Spot instances
    use_spot_instances: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="使用Spot实例")
    spot_interruption_behavior: Mapped[SpotInterruptionBehavior | None] = mapped_column(
        Enum(SpotInterruptionBehavior), nullable=True, comment="Spot中断行为"
    )

    # Scheduling
    priority: Mapped[JobPriority] = mapped_column(
        Enum(JobPriority), nullable=False, default=JobPriority.MEDIUM, index=True, comment="任务优先级"
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), nullable=False, default=JobStatus.SUBMITTED, index=True, comment="任务状态"
    )

    # HyperPod/Kueue status
    hyperpod_job_arn: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="HyperPod训练任务ARN")
    hyperpod_status: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="HyperPod状态")
    kueue_workload_name: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="Kueue Workload名称")
    kueue_status: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="Kueue状态")

    # Pod statistics
    total_pods: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="总Pod数量")
    running_pods: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="运行中Pod数量")
    failed_pods: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="失败Pod数量")
    preemption_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="累计被抢占次数")

    # Training metrics
    current_epoch: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="当前训练轮次")
    current_step: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="当前训练步数")
    latest_loss: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=10, scale=6), nullable=True, comment="最新损失值"
    )
    latest_accuracy: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=5, scale=4), nullable=True, comment="最新准确率"
    )

    # Time statistics
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True, comment="提交时间")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True, comment="开始时间")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True, comment="完成时间")
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="运行时长(秒)")

    # Cost statistics
    total_gpu_hours: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=True, comment="总GPU时"
    )
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=True, comment="预估成本(USD)"
    )

    # Error information
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    failure_reason: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="失败原因")

    # Relationships
    owner: Mapped["UserModel"] = relationship("UserModel", back_populates="training_jobs")
    checkpoints: Mapped[list["CheckpointModel"]] = relationship(
        "CheckpointModel",
        back_populates="training_job",
        cascade="all, delete-orphan",
        foreign_keys="[CheckpointModel.training_job_id]",
    )
    models: Mapped[list["ModelModel"]] = relationship("ModelModel", back_populates="training_job")

    __table_args__ = ({"comment": "训练任务表"},)
