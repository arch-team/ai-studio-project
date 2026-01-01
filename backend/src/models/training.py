"""训练任务相关模型

定义训练任务、配置和指标的数据模型
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .user import Project, User
    from .model import Model


class TrainingJobStatus(str, enum.Enum):
    """训练任务状态"""

    PENDING = "PENDING"  # 等待中
    QUEUED = "QUEUED"  # 已排队
    RUNNING = "RUNNING"  # 运行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 失败
    CANCELLED = "CANCELLED"  # 已取消
    TIMEOUT = "TIMEOUT"  # 超时


class TrainingJobType(str, enum.Enum):
    """训练任务类型"""

    SINGLE_NODE = "SINGLE_NODE"  # 单节点训练
    DISTRIBUTED_DATA_PARALLEL = "DISTRIBUTED_DATA_PARALLEL"  # 数据并行
    DISTRIBUTED_MODEL_PARALLEL = "DISTRIBUTED_MODEL_PARALLEL"  # 模型并行
    HYBRID_PARALLEL = "HYBRID_PARALLEL"  # 混合并行


class FrameworkType(str, enum.Enum):
    """训练框架类型"""

    PYTORCH = "PYTORCH"
    TENSORFLOW = "TENSORFLOW"
    JFLUX = "JFLUX"
    DEEPSPEED = "DEEPSPEED"
    MEGATRON = "MEGATRON"


class TrainingJob(Base, TimestampMixin, SoftDeleteMixin):
    """训练任务模型

    记录训练任务的基本信息、配置和状态
    """

    __tablename__ = "training_jobs"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="任务名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="任务描述")
    status: Mapped[TrainingJobStatus] = mapped_column(
        Enum(TrainingJobStatus), nullable=False, default=TrainingJobStatus.PENDING, comment="任务状态"
    )
    job_type: Mapped[TrainingJobType] = mapped_column(
        Enum(TrainingJobType), nullable=False, comment="任务类型"
    )
    framework: Mapped[FrameworkType] = mapped_column(
        Enum(FrameworkType), nullable=False, comment="训练框架"
    )

    # 关联关系
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, comment="项目ID"
    )
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="创建者ID"
    )

    # Kubernetes相关
    k8s_namespace: Mapped[str] = mapped_column(
        String(63), nullable=False, comment="K8S命名空间"
    )
    k8s_job_name: Mapped[str | None] = mapped_column(
        String(253), nullable=True, comment="K8S Job名称"
    )
    k8s_pod_names: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, comment="K8S Pod名称列表"
    )

    # Kueue Gang Scheduling支持
    priority: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default="normal", comment="Kueue优先级: low, normal, high"
    )
    queue_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Kueue LocalQueue名称,默认使用项目队列"
    )

    # 时间信息
    queued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="排队时间"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="开始时间"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="完成时间"
    )

    # 失败信息
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="退出码")

    # 重试机制
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="重试次数"
    )
    last_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后重试时间"
    )

    # 关系
    project: Mapped["Project"] = relationship("Project", back_populates="training_jobs")
    creator: Mapped["User"] = relationship("User", back_populates="training_jobs")
    config: Mapped["TrainingJobConfig"] = relationship(
        "TrainingJobConfig", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    metrics: Mapped[list["TrainingJobMetrics"]] = relationship(
        "TrainingJobMetrics", back_populates="job", cascade="all, delete-orphan"
    )
    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        "Checkpoint", back_populates="job", cascade="all, delete-orphan"
    )
    generated_models: Mapped[list["Model"]] = relationship(
        "Model", back_populates="source_training_job"
    )

    def __repr__(self) -> str:
        return f"<TrainingJob(id={self.id}, name={self.name}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """任务是否处于活跃状态（可停止的状态）

        PENDING状态任务还未调度，应直接删除而非停止
        只有QUEUED和RUNNING状态才需要停止操作
        """
        return self.status in {
            TrainingJobStatus.QUEUED,
            TrainingJobStatus.RUNNING,
        }

    @property
    def is_terminal(self) -> bool:
        """任务是否处于终止状态"""
        return self.status in {
            TrainingJobStatus.COMPLETED,
            TrainingJobStatus.FAILED,
            TrainingJobStatus.CANCELLED,
            TrainingJobStatus.TIMEOUT,
        }

    @property
    def duration_seconds(self) -> int | None:
        """任务执行时长(秒)"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None


class TrainingJobConfig(Base, TimestampMixin):
    """训练任务配置模型

    存储训练任务的详细配置信息
    """

    __tablename__ = "training_job_configs"

    # 关联训练任务
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("training_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="训练任务ID",
    )

    # 资源配置
    node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="节点数量")
    gpu_per_node: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="每节点GPU数")
    cpu_per_node: Mapped[int] = mapped_column(Integer, nullable=False, default=8, comment="每节点CPU数")
    memory_per_node_gb: Mapped[int] = mapped_column(
        Integer, nullable=False, default=32, comment="每节点内存(GB)"
    )
    gpu_type: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="GPU型号")

    # 训练配置
    docker_image: Mapped[str] = mapped_column(String(500), nullable=False, comment="Docker镜像")
    command: Mapped[list[str]] = mapped_column(JSON, nullable=False, comment="执行命令")
    args: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, comment="命令参数")
    env_vars: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True, comment="环境变量")

    # 数据配置
    dataset_path: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="数据集路径")
    checkpoint_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="检查点路径"
    )
    output_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="输出路径")

    # 超参数
    hyperparameters: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="超参数")

    # 分布式配置
    distributed_config: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="分布式训练配置"
    )

    # 超时和重试
    timeout_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="超时时间(秒)"
    )
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="最大重试次数")

    # 关系
    job: Mapped["TrainingJob"] = relationship("TrainingJob", back_populates="config")

    def __repr__(self) -> str:
        return f"<TrainingJobConfig(job_id={self.job_id}, nodes={self.node_count}, gpus={self.gpu_per_node})>"


class TrainingJobMetrics(Base, TimestampMixin):
    """训练任务指标模型

    记录训练过程中的指标数据(loss, accuracy等)
    """

    __tablename__ = "training_job_metrics"

    # 关联训练任务
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_jobs.id", ondelete="CASCADE"), nullable=False, comment="训练任务ID"
    )

    # 指标数据
    epoch: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="训练轮次")
    step: Mapped[int] = mapped_column(Integer, nullable=False, comment="训练步数")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="记录时间"
    )

    # 通用指标(JSON存储,支持任意指标)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, comment="指标数据")

    # 常用指标字段(方便查询)
    loss: Mapped[float | None] = mapped_column(String(50), nullable=True, comment="损失值")
    accuracy: Mapped[float | None] = mapped_column(String(50), nullable=True, comment="准确率")
    learning_rate: Mapped[float | None] = mapped_column(String(50), nullable=True, comment="学习率")

    # 关系
    job: Mapped["TrainingJob"] = relationship("TrainingJob", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<TrainingJobMetrics(job_id={self.job_id}, step={self.step}, loss={self.loss})>"


class CheckpointStorageType(str, enum.Enum):
    """检查点存储类型"""

    LOCAL = "LOCAL"  # 本地NVMe存储
    FSX = "FSX"  # FSx for Lustre
    S3 = "S3"  # S3长期存储


class Checkpoint(Base, TimestampMixin):
    """检查点模型

    记录训练过程中保存的模型检查点
    支持分层存储策略: Local NVMe -> FSx -> S3
    """

    __tablename__ = "checkpoints"

    # 关联训练任务
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_jobs.id", ondelete="CASCADE"), nullable=False, comment="训练任务ID"
    )

    # 检查点信息
    step: Mapped[int] = mapped_column(Integer, nullable=False, comment="训练步数")
    epoch: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="训练轮次")

    # 存储信息
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="存储路径")
    storage_type: Mapped[CheckpointStorageType] = mapped_column(
        Enum(CheckpointStorageType), nullable=False, comment="存储类型"
    )
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="文件大小(字节)")

    # 元数据
    checkpoint_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="检查点元数据")
    checkpoint_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="训练指标快照")

    # 关系
    job: Mapped["TrainingJob"] = relationship("TrainingJob", back_populates="checkpoints")

    def __repr__(self) -> str:
        return f"<Checkpoint(id={self.id}, job_id={self.job_id}, step={self.step}, storage={self.storage_type.value})>"


__all__ = [
    "TrainingJob",
    "TrainingJobConfig",
    "TrainingJobMetrics",
    "Checkpoint",
    "TrainingJobStatus",
    "TrainingJobType",
    "FrameworkType",
    "CheckpointStorageType",
]
