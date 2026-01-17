"""User ORM model - Platform user information with IAM integration."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure import Base
from src.shared.utils import utc_now

from ...domain.value_objects import AuthType, UserRole, UserStatus

if TYPE_CHECKING:
    from .login_attempt_model import LoginAttemptModel
    from .password_history_model import PasswordHistoryModel
    from src.modules.training.infrastructure.models import TrainingJobModel
    from src.modules.models.infrastructure.models import ModelModel
    from src.modules.spaces.infrastructure.models import DevelopmentSpaceModel
    from src.modules.quotas.infrastructure.models import ResourceQuotaModel


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=utc_now,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        comment="更新时间",
    )


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
    display_name: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="显示名称",
    )

    # IAM integration
    iam_identity_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        comment="AWS IAM Identity Center用户ID",
    )
    iam_groups: Mapped[list | None] = mapped_column(
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
    resource_quota_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("resource_quotas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联的资源配额ID",
    )

    # Login tracking
    last_login_at: Mapped[datetime | None] = mapped_column(
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
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="密码哈希(本地账号)",
    )
    password_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="密码过期时间",
    )
    locked_until: Mapped[datetime | None] = mapped_column(
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
    training_jobs: Mapped[list["TrainingJobModel"]] = relationship(
        "TrainingJobModel",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    models: Mapped[list["ModelModel"]] = relationship(
        "ModelModel",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    development_spaces: Mapped[list["DevelopmentSpaceModel"]] = relationship(
        "DevelopmentSpaceModel",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    resource_quota: Mapped["ResourceQuotaModel | None"] = relationship(
        "ResourceQuotaModel",
        back_populates="users",
        foreign_keys=[resource_quota_id],
    )

    __table_args__ = ({"comment": "用户表"},)
