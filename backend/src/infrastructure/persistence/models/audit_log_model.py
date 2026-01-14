"""AuditLog ORM model - Audit trail for platform operations."""

import enum
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text, event, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.utils import utc_now

if TYPE_CHECKING:
    from src.infrastructure.persistence.models.user_model import UserModel


class OperationType(enum.Enum):
    """Operation type enumeration."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"


class ResourceType(enum.Enum):
    """Resource type enumeration."""

    TRAINING_JOB = "training_job"
    DATASET = "dataset"
    MODEL = "model"
    USER = "user"
    QUOTA = "quota"
    SPACE = "space"


class AuditStatus(enum.Enum):
    """Audit log status enumeration."""

    SUCCESS = "success"
    FAILED = "failed"


class AuditLogModel(Base):
    """Audit log ORM model."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="审计日志ID",
    )

    # User association
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="用户ID",
    )

    # Operation details
    operation_type: Mapped[OperationType] = mapped_column(
        Enum(OperationType),
        nullable=False,
        index=True,
        comment="操作类型",
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType),
        nullable=False,
        index=True,
        comment="资源类型",
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="资源ID",
    )

    # Request/Response data
    request_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="请求数据",
    )
    response_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="响应数据",
    )

    # Client information
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IP地址",
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="User-Agent",
    )

    # Status
    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus),
        nullable=False,
        default=AuditStatus.SUCCESS,
        index=True,
        comment="操作状态",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="创建时间",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        index=True,
        comment="过期时间(90天后)",
    )

    # Relationships
    user: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        back_populates="audit_logs",
    )

    __table_args__ = ({"comment": "审计日志表"},)


@event.listens_for(AuditLogModel, "before_insert")
def set_expires_at(mapper, connection, target):
    """Auto-set expires_at to 90 days after created_at."""
    if target.expires_at is None:
        target.expires_at = utc_now() + timedelta(days=90)
