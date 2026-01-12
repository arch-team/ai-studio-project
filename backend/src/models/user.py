"""User model - SQLAlchemy 2.0 async model.

Task: T011 - 创建 SQLAlchemy User 模型
使用 Pydantic v2 schema 验证,关联 resource_quotas
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, String, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.audit_log import AuditLog
    from src.models.resource_quota import ResourceQuota
    from src.models.space import Space


class UserStatus(str, PyEnum):
    """用户状态枚举."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserRole(str, PyEnum):
    """用户角色枚举 (与 RBAC 策略对应).

    角色层级: ADMIN > PROJECT_MANAGER > ENGINEER > VIEWER
    支持比较运算符: admin >= viewer → True
    """

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"

    @classmethod
    def get_hierarchy(cls) -> dict["UserRole", int]:
        """获取角色层级映射 (数值越高权限越大)."""
        return {
            cls.ADMIN: 4,
            cls.PROJECT_MANAGER: 3,
            cls.ENGINEER: 2,
            cls.VIEWER: 1,
        }

    @classmethod
    def get_level(cls, role: "UserRole") -> int:
        """获取指定角色的层级数值."""
        return cls.get_hierarchy().get(role, 0)

    def __ge__(self, other: "UserRole") -> bool:
        """比较运算符: 判断当前角色层级是否 >= 另一角色."""
        if not isinstance(other, UserRole):
            return NotImplemented
        return self.get_level(self) >= self.get_level(other)

    def __gt__(self, other: "UserRole") -> bool:
        """比较运算符: 判断当前角色层级是否 > 另一角色."""
        if not isinstance(other, UserRole):
            return NotImplemented
        return self.get_level(self) > self.get_level(other)

    def __le__(self, other: "UserRole") -> bool:
        """比较运算符: 判断当前角色层级是否 <= 另一角色."""
        if not isinstance(other, UserRole):
            return NotImplemented
        return self.get_level(self) <= self.get_level(other)

    def __lt__(self, other: "UserRole") -> bool:
        """比较运算符: 判断当前角色层级是否 < 另一角色."""
        if not isinstance(other, UserRole):
            return NotImplemented
        return self.get_level(self) < self.get_level(other)


class User(Base):
    """用户模型 - 存储平台用户信息,支持 AWS IAM Identity Center (SSO) 集成."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uk_users_username"),
        UniqueConstraint("email", name="uk_users_email"),
        UniqueConstraint("iam_identity_id", name="uk_users_iam_identity_id"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
            "comment": "用户表",
        },
    )

    # 主键 (UUID)
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="用户ID (UUID)",
    )

    # 身份信息
    username: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="用户名 (IAM 用户名)",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="邮箱地址",
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="显示名称",
    )

    # IAM 集成
    iam_identity_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="AWS IAM Identity Center 用户ID",
    )
    iam_groups: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="IAM 用户组列表 (JSON 数组)",
    )

    # 用户状态
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"),
        nullable=False,
        default=UserStatus.ACTIVE,
        comment="用户状态",
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.ENGINEER,
        comment="用户角色",
    )

    # 资源配额 (外键)
    resource_quota_id: Mapped[Optional[int]] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
        comment="关联的资源配额ID",
    )

    # 审计字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间",
    )

    # 关联关系
    resource_quota: Mapped[Optional["ResourceQuota"]] = relationship(
        "ResourceQuota",
        back_populates="users",
        foreign_keys=[resource_quota_id],
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    spaces: Mapped[List["Space"]] = relationship(
        "Space",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, username='{self.username}', role={self.role.value})>"

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has at least the required role level.

        Role hierarchy: admin > project_manager > engineer > viewer

        Args:
            required_role: The minimum role required

        Returns:
            True if user has sufficient permissions
        """
        return self.role >= required_role
