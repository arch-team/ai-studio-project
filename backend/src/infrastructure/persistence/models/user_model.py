"""User ORM model - Platform user information with IAM integration."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.infrastructure.persistence.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.persistence.models.audit_log_model import AuditLogModel
    from src.infrastructure.persistence.models.development_space_model import (
        DevelopmentSpaceModel,
    )
    from src.infrastructure.persistence.models.login_attempt_model import (
        LoginAttemptModel,
    )
    from src.infrastructure.persistence.models.password_history_model import (
        PasswordHistoryModel,
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


class AuthType(enum.Enum):
    """Authentication type enumeration."""

    SSO = "sso"
    LOCAL = "local"


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

    # Authentication fields (for local accounts)
    auth_type: Mapped[AuthType] = mapped_column(
        Enum(AuthType),
        nullable=False,
        default=AuthType.SSO,
        server_default="sso",
        comment="认证类型",
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="密码哈希(本地账号)",
    )
    password_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="密码过期时间",
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="账号锁定截止时间",
    )
    failed_login_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="连续登录失败次数",
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
    password_history: Mapped[list["PasswordHistoryModel"]] = relationship(
        "PasswordHistoryModel",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(PasswordHistoryModel.created_at)",
    )
    login_attempts: Mapped[list["LoginAttemptModel"]] = relationship(
        "LoginAttemptModel",
        back_populates="user",
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

    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def is_password_expired(self) -> bool:
        """Check if password has expired."""
        if self.password_expires_at is None:
            return False
        return datetime.utcnow() > self.password_expires_at

    def is_local_account(self) -> bool:
        """Check if this is a local authentication account."""
        return self.auth_type == AuthType.LOCAL
