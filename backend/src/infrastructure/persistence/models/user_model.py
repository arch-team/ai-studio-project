"""User ORM model - Platform user information with IAM integration."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.infrastructure.persistence.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.persistence.models.audit_log_model import AuditLogModel
    from src.infrastructure.persistence.models.development_space_model import (
        DevelopmentSpaceModel,
    )
    from src.infrastructure.persistence.models.resource_quota_model import (
        ResourceQuotaModel,
    )


class UserStatus(enum.Enum):
    """User status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserRole(enum.Enum):
    """User role enumeration."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class UserModel(Base, TimestampMixin):
    """User ORM model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="用户ID",
    )

    # Identity information
    username: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名(IAM用户名)",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="邮箱地址",
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="显示名称",
    )

    # IAM integration
    iam_identity_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        comment="AWS IAM Identity Center用户ID",
    )
    iam_groups: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="IAM用户组列表",
    )

    # User status and role
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        nullable=False,
        default=UserStatus.ACTIVE,
        index=True,
        comment="用户状态",
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.ENGINEER,
        comment="用户角色",
    )

    # Resource quota association
    resource_quota_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("resource_quotas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联的资源配额ID",
    )

    # Login tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="最后登录时间",
    )

    # Relationships
    resource_quota: Mapped[Optional["ResourceQuotaModel"]] = relationship(
        "ResourceQuotaModel",
        back_populates="users",
        foreign_keys=[resource_quota_id],
    )
    audit_logs: Mapped[list["AuditLogModel"]] = relationship(
        "AuditLogModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    development_spaces: Mapped[list["DevelopmentSpaceModel"]] = relationship(
        "DevelopmentSpaceModel",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    __table_args__ = ({"comment": "用户表"},)

    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE

    def has_admin_privileges(self) -> bool:
        """Check if user has admin privileges."""
        return self.role == UserRole.ADMIN

    def can_create_training_job(self) -> bool:
        """Check if user can create training jobs."""
        return self.is_active() and self.role in (
            UserRole.ADMIN,
            UserRole.PROJECT_MANAGER,
            UserRole.ENGINEER,
        )
