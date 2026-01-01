"""模型管理数据模型

管理训练生成的模型文件、版本和元数据
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from models.training import TrainingJob
    from models.user import Project, User


class ModelStatus(str, enum.Enum):
    """模型状态"""

    UPLOADING = "UPLOADING"  # 上传中
    PROCESSING = "PROCESSING"  # 处理中
    AVAILABLE = "AVAILABLE"  # 可用
    FAILED = "FAILED"  # 失败
    ARCHIVED = "ARCHIVED"  # 已归档


class ModelFramework(str, enum.Enum):
    """模型框架"""

    PYTORCH = "PYTORCH"
    TENSORFLOW = "TENSORFLOW"
    ONNX = "ONNX"
    JFLUX = "JFLUX"
    HUGGINGFACE = "HUGGINGFACE"
    CUSTOM = "CUSTOM"


class Model(Base, TimestampMixin, SoftDeleteMixin):
    """模型主表

    管理模型的基本信息和版本
    """

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    framework: Mapped[ModelFramework] = mapped_column(
        Enum(ModelFramework), nullable=False, index=True
    )
    task_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True, comment="任务类型: classification, detection等"
    )

    # 关联关系
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 源训练任务(可选)
    source_training_job_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("training_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 标签和元数据
    tags: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, comment="模型标签"
    )
    model_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="自定义元数据"
    )

    # 最新版本信息(冗余字段,提高查询性能)
    latest_version: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="最新版本号"
    )
    latest_version_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="最新版本ID"
    )

    # 关系
    project: Mapped["Project"] = relationship("Project", back_populates="models")
    creator: Mapped["User"] = relationship(
        "User", back_populates="models", foreign_keys=[creator_id]
    )
    source_training_job: Mapped["TrainingJob | None"] = relationship(
        "TrainingJob", back_populates="generated_models"
    )
    versions: Mapped[list["ModelVersion"]] = relationship(
        "ModelVersion", back_populates="model", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Model(id={self.id}, name={self.name}, framework={self.framework})>"


class ModelVersion(Base, TimestampMixin, SoftDeleteMixin):
    """模型版本表

    管理模型的版本信息和存储路径
    """

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 版本信息
    model_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="版本号: v1.0.0, v1.1.0等"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 状态
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus), nullable=False, default=ModelStatus.PROCESSING, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 存储信息
    storage_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="模型文件存储路径"
    )
    storage_size_bytes: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="模型文件大小(字节)"
    )
    checksum_md5: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="MD5校验和"
    )

    # 模型信息
    model_format: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="模型格式: pth, ckpt, pb, onnx等"
    )
    model_architecture: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="模型架构: ResNet50, BERT等"
    )

    # 性能指标
    metrics: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="性能指标: accuracy, loss等"
    )
    hyperparameters: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="训练超参数"
    )

    # 依赖信息
    dependencies: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="依赖包版本信息"
    )

    # 发布信息
    is_published: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="是否发布"
    )
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    published_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # 关系
    model: Mapped["Model"] = relationship("Model", back_populates="versions")
    published_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[published_by_id]
    )

    def __repr__(self) -> str:
        return f"<ModelVersion(id={self.id}, model_id={self.model_id}, version={self.version})>"


class ModelDeployment(Base, TimestampMixin, SoftDeleteMixin):
    """模型部署记录表

    记录模型版本的部署历史
    """

    __tablename__ = "model_deployments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 关联
    model_version_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("model_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deployed_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # 部署信息
    deployment_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    deployment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="部署类型: online, batch, edge等"
    )
    endpoint_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="部署端点URL"
    )

    # K8S部署信息
    k8s_namespace: Mapped[str | None] = mapped_column(String(63), nullable=True)
    k8s_deployment_name: Mapped[str | None] = mapped_column(String(253), nullable=True)

    # 状态
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING", index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # 配置
    deployment_config: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="部署配置"
    )

    def __repr__(self) -> str:
        return f"<ModelDeployment(id={self.id}, name={self.deployment_name})>"


__all__ = [
    "Model",
    "ModelVersion",
    "ModelDeployment",
    "ModelStatus",
    "ModelFramework",
]
