"""DevelopmentSpace ORM model - SageMaker Spaces for online development."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.spaces.domain.value_objects import (
    SpaceBackend,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.shared.infrastructure.database import Base
from src.shared.infrastructure.models.base import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from src.modules.auth.infrastructure.models import UserModel


class DevelopmentSpaceModel(Base, TimestampMixin, SoftDeleteMixin):
    """Development space ORM model."""

    __tablename__ = "development_spaces"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="空间ID(UUID)",
    )

    # Space identification
    space_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="空间名称",
    )

    # Owner association
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所有者用户ID",
    )

    # Space configuration
    instance_type: Mapped[SpaceInstanceType] = mapped_column(
        Enum(SpaceInstanceType),
        nullable=False,
        default=SpaceInstanceType.ML_G5_XLARGE,
        comment="实例类型",
    )
    space_type: Mapped[SpaceType] = mapped_column(
        Enum(SpaceType),
        nullable=False,
        default=SpaceType.JUPYTER,
        comment="空间类型",
    )
    backend: Mapped[SpaceBackend] = mapped_column(
        Enum(SpaceBackend),
        nullable=False,
        default=SpaceBackend.STUDIO,
        index=True,
        comment="开发环境后端类型",
    )

    # HyperPod backend 专属字段（仅 backend=HYPERPOD 使用）
    namespace: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="HyperPod CRD namespace",
    )
    queue_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Kueue local queue",
    )
    workspace_template: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="WorkspaceTemplate 引用",
    )

    # Status
    status: Mapped[SpaceStatus] = mapped_column(
        Enum(SpaceStatus),
        nullable=False,
        default=SpaceStatus.PENDING,
        index=True,
        comment="空间状态",
    )

    # Storage
    storage_size_gb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
        comment="存储大小(GB)",
    )

    # SageMaker integration
    lifecycle_config_arn: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Lifecycle配置ARN",
    )
    sagemaker_space_arn: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        unique=True,
        comment="SageMaker Space ARN",
    )

    # Relationships
    owner: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="development_spaces",
    )

    __table_args__ = ({"comment": "开发空间表"},)
