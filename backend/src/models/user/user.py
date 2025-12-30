"""用户模型

管理平台用户信息和认证
"""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin

if TYPE_CHECKING:
    from models.user.team import Team
    from models.user.project import Project
    from models.training import TrainingJob
    from models.model import Model


class UserRole(str, Enum):
    """用户角色枚举"""

    ADMIN = "admin"  # 平台管理员
    PROJECT_MANAGER = "project_manager"  # 项目经理
    ALGORITHM_ENGINEER = "algorithm_engineer"  # 算法工程师
    DATA_ENGINEER = "data_engineer"  # 数据工程师
    VIEWER = "viewer"  # 查看者


class UserStatus(str, Enum):
    """用户状态枚举"""

    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 未激活
    SUSPENDED = "suspended"  # 暂停


class User(Base, SoftDeleteMixin):
    """用户模型

    Attributes:
        username: 用户名（唯一）
        email: 邮箱地址（唯一）
        hashed_password: 密码哈希
        full_name: 全名
        role: 用户角色
        status: 用户状态
        is_active: 是否激活
        is_superuser: 是否超级用户
        teams: 所属团队列表
        owned_projects: 拥有的项目列表
    """

    __tablename__ = "users"

    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, comment="邮箱地址"
    )

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")

    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="全名")

    # 角色和权限
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.VIEWER,
        nullable=False,
        comment="用户角色",
    )

    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
        comment="用户状态",
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="是否激活")

    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否超级用户"
    )

    # 关系
    # teams: Mapped[list["Team"]] = relationship(
    #     "Team", secondary="team_members", back_populates="members"
    # )

    # owned_projects: Mapped[list["Project"]] = relationship(
    #     "Project", back_populates="owner", foreign_keys="Project.owner_id"
    # )

    training_jobs: Mapped[list["TrainingJob"]] = relationship(
        "TrainingJob", back_populates="creator", foreign_keys="TrainingJob.creator_id"
    )

    models: Mapped[list["Model"]] = relationship(
        "Model", back_populates="creator", foreign_keys="Model.creator_id"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username!r}, email={self.email!r}, role={self.role.value})"

    @property
    def is_admin(self) -> bool:
        """是否为管理员

        Returns:
            bool: True表示是管理员或超级用户
        """
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def can_manage_resources(self) -> bool:
        """是否可以管理资源

        Returns:
            bool: True表示可以管理资源（管理员或项目经理）
        """
        return self.role in [UserRole.ADMIN, UserRole.PROJECT_MANAGER]

    @property
    def can_submit_training_jobs(self) -> bool:
        """是否可以提交训练任务

        Returns:
            bool: True表示可以提交训练任务
        """
        return self.role in [
            UserRole.ADMIN,
            UserRole.PROJECT_MANAGER,
            UserRole.ALGORITHM_ENGINEER,
        ]

    @property
    def can_manage_datasets(self) -> bool:
        """是否可以管理数据集

        Returns:
            bool: True表示可以管理数据集
        """
        return self.role in [
            UserRole.ADMIN,
            UserRole.PROJECT_MANAGER,
            UserRole.DATA_ENGINEER,
        ]
