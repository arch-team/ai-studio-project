"""ResourceQuota ORM model - Resource quota definitions for users/teams."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.quotas.domain.value_objects import QuotaStatus, QuotaType
from src.shared.infrastructure.database import Base
from src.shared.infrastructure.models import TimestampMixin

if TYPE_CHECKING:
    from src.modules.auth.infrastructure.models import UserModel


class ResourceQuotaModel(Base, TimestampMixin):
    """Resource quota ORM model."""

    __tablename__ = "resource_quotas"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="配额ID",
    )

    # Quota identification
    name: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="配额名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="配额描述",
    )

    # Quota type
    quota_type: Mapped[QuotaType] = mapped_column(
        Enum(QuotaType),
        nullable=False,
        default=QuotaType.USER,
        index=True,
        comment="配额类型",
    )

    # CPU quota (unit: vCPU)
    max_cpu_cores: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="最大CPU核心数",
    )
    reserved_cpu_cores: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="预留CPU核心数",
    )

    # GPU quota
    max_gpu_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="最大GPU数量",
    )
    reserved_gpu_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="预留GPU数量",
    )
    gpu_types: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="允许的GPU类型列表",
    )

    # Memory quota (unit: GB)
    max_memory_gb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="最大内存(GB)",
    )
    reserved_memory_gb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="预留内存(GB)",
    )

    # Storage quota (unit: GB)
    max_storage_gb: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="最大存储空间(GB)",
    )

    # Training job quota
    max_concurrent_jobs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="最大并发训练任务数",
    )
    max_total_jobs: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="总训练任务数限制",
    )

    # Spot instance quota
    max_spot_instances: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="最大Spot实例数",
    )

    # Quota status
    status: Mapped[QuotaStatus] = mapped_column(
        Enum(QuotaStatus),
        nullable=False,
        default=QuotaStatus.ACTIVE,
        index=True,
        comment="配额状态",
    )

    # Validity period
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        comment="生效时间",
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="过期时间",
    )

    # Audit fields
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建人用户ID",
    )

    # Relationships
    users: Mapped[list["UserModel"]] = relationship(
        "UserModel",
        back_populates="resource_quota",
        foreign_keys="UserModel.resource_quota_id",
    )

    __table_args__ = ({"comment": "资源配额表"},)
