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

from src.core.database import Base
from src.domain.entities.training_job import (
    DistributionStrategy,
    JobPriority,
    JobStatus,
    SpotInterruptionBehavior,
)
from src.infrastructure.persistence.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.persistence.models.checkpoint_model import CheckpointModel
    from src.infrastructure.persistence.models.ml_model import ModelModel
    from src.infrastructure.persistence.models.user_model import UserModel


class TrainingJobModel(Base, TimestampMixin):
    """Training job ORM model."""

    __tablename__ = "training_jobs"

    # Primary key
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="训练任务ID",
    )

    # Job identification
    job_name: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="任务名称 (HyperPod Job 名称)",
    )
    display_name: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="显示名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="任务描述",
    )

    # Owner
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所有者用户ID",
    )

    # Training configuration
    image_uri: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Docker 镜像 URI",
    )
    instance_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="实例类型 (例如: ml.p4d.24xlarge)",
    )
    node_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="节点数量",
    )
    tasks_per_node: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="每节点任务数 (GPU 数量)",
    )

    # Entrypoint and environment
    entrypoint_command: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        comment="启动命令 (JSON 数组)",
    )
    environment_variables: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="环境变量 (JSON 对象)",
    )

    # Dataset configuration
    dataset_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="关联数据集ID",
    )
    data_mount_path: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="数据挂载路径 (例如: /data)",
    )

    # Checkpoint configuration
    checkpoint_mount_path: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="检查点挂载路径 (例如: /checkpoints)",
    )
    checkpoint_interval: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="检查点保存间隔 (epoch)",
    )

    # Auto-recovery configuration (HyperPod Elastic Agent)
    auto_resume_checkpoint_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("checkpoints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="自动恢复检查点ID (HyperPod Elastic Agent 恢复时使用)",
    )

    # Training parameters
    hyperparameters: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="超参数 (JSON 对象)",
    )
    max_epochs: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="最大训练轮数",
    )
    batch_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="批次大小",
    )
    learning_rate: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=10, scale=8),
        nullable=True,
        comment="学习率",
    )

    # Distribution strategy
    distribution_strategy: Mapped[DistributionStrategy] = mapped_column(
        Enum(DistributionStrategy),
        nullable=False,
        default=DistributionStrategy.DDP,
        server_default="DDP",
        comment="分布式策略",
    )
    mixed_precision: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="是否使用混合精度训练 (AMP)",
    )

    # Spot instance configuration
    use_spot_instances: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="是否使用 Spot 实例",
    )
    spot_interruption_behavior: Mapped[SpotInterruptionBehavior | None] = mapped_column(
        Enum(SpotInterruptionBehavior),
        nullable=True,
        default=SpotInterruptionBehavior.STOP,
        server_default="STOP",
        comment="Spot 中断行为",
    )

    # Priority (FR-004 preemptive scheduling)
    priority: Mapped[JobPriority] = mapped_column(
        Enum(JobPriority),
        nullable=False,
        default=JobPriority.MEDIUM,
        server_default="MEDIUM",
        index=True,
        comment="任务优先级 (用于抢占式调度)",
    )

    # Job status (spec.md state machine)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        nullable=False,
        default=JobStatus.SUBMITTED,
        server_default="SUBMITTED",
        index=True,
        comment="任务状态",
    )

    # HyperPod/Kueue status mapping
    hyperpod_status: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="HyperPod Job 原始状态",
    )
    kueue_workload_name: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        comment="Kueue Workload 名称",
    )
    kueue_status: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Kueue Workload 状态",
    )

    # Pod statistics
    total_pods: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="总 Pod 数量",
    )
    running_pods: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="运行中 Pod 数量",
    )
    failed_pods: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="失败 Pod 数量",
    )

    # Preemption statistics
    preemption_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="累计被抢占次数",
    )

    # Training metrics (latest values)
    current_epoch: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="当前训练轮次",
    )
    current_step: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="当前训练步数",
    )
    latest_loss: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=10, scale=6),
        nullable=True,
        comment="最新损失值",
    )
    latest_accuracy: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=5, scale=4),
        nullable=True,
        comment="最新准确率",
    )

    # Time statistics
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="提交时间",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="开始时间",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="完成时间",
    )
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="运行时长 (秒)",
    )

    # Resource statistics
    total_gpu_hours: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=12, scale=2),
        nullable=True,
        comment="总 GPU 时",
    )
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(
        DECIMAL(precision=12, scale=2),
        nullable=True,
        comment="预估成本 (USD)",
    )

    # Error information
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )
    failure_reason: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="失败原因",
    )

    # Relationships
    owner: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="training_jobs",
    )
    checkpoints: Mapped[list["CheckpointModel"]] = relationship(
        "CheckpointModel",
        back_populates="training_job",
        cascade="all, delete-orphan",
    )
    models: Mapped[list["ModelModel"]] = relationship(
        "ModelModel",
        back_populates="training_job",
    )

    __table_args__ = ({"comment": "训练任务表"},)

    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == JobStatus.RUNNING

    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    def can_pause(self) -> bool:
        """Check if job can be paused."""
        return self.status == JobStatus.RUNNING

    def can_resume(self) -> bool:
        """Check if job can be resumed."""
        return self.status in (JobStatus.PAUSED, JobStatus.PREEMPTED)
