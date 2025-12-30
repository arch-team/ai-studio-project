"""项目模型

管理训练项目信息
"""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin

if TYPE_CHECKING:
    from models.user.user import User
    from models.user.team import Team


class ProjectStatus(str, Enum):
    """项目状态枚举"""

    ACTIVE = "active"  # 活跃
    ARCHIVED = "archived"  # 已归档
    SUSPENDED = "suspended"  # 暂停


class Project(Base, SoftDeleteMixin):
    """项目模型

    Attributes:
        name: 项目名称
        description: 项目描述
        status: 项目状态
        owner_id: 项目所有者ID
        team_id: 所属团队ID
        owner: 项目所有者
        team: 所属团队
        namespace: Kubernetes命名空间
    """

    __tablename__ = "projects"

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False, comment="项目名称"
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="项目描述")

    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus),
        default=ProjectStatus.ACTIVE,
        nullable=False,
        comment="项目状态",
    )

    # 关联关系
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所有者ID"
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, comment="团队ID"
    )

    # Kubernetes命名空间
    namespace: Mapped[str] = mapped_column(
        String(63),  # K8S命名空间最大长度
        unique=True,
        index=True,
        nullable=False,
        comment="Kubernetes命名空间",
    )

    # 关系
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])

    team: Mapped["Team"] = relationship("Team", back_populates="projects")

    # training_jobs: Mapped[list["TrainingJob"]] = relationship(
    #     "TrainingJob", back_populates="project"
    # )

    # datasets: Mapped[list["Dataset"]] = relationship(
    #     "Dataset", back_populates="project"
    # )

    def __repr__(self) -> str:
        return f"Project(id={self.id}, name={self.name!r}, namespace={self.namespace!r})"

    @property
    def is_active(self) -> bool:
        """项目是否活跃

        Returns:
            bool: True表示活跃
        """
        return self.status == ProjectStatus.ACTIVE

    @property
    def is_archived(self) -> bool:
        """项目是否已归档

        Returns:
            bool: True表示已归档
        """
        return self.status == ProjectStatus.ARCHIVED

    def can_access(self, user_id: int) -> bool:
        """检查用户是否可以访问项目

        Args:
            user_id: 用户ID

        Returns:
            bool: True表示可以访问
        """
        # 所有者可以访问
        if self.owner_id == user_id:
            return True

        # 团队成员可以访问
        if self.team and self.team.is_member(user_id):
            return True

        return False

    def can_manage(self, user_id: int) -> bool:
        """检查用户是否可以管理项目

        Args:
            user_id: 用户ID

        Returns:
            bool: True表示可以管理
        """
        # 所有者可以管理
        if self.owner_id == user_id:
            return True

        # 团队所有者可以管理
        if self.team and self.team.is_owner(user_id):
            return True

        return False

    @staticmethod
    def generate_namespace(team_name: str, project_name: str) -> str:
        """生成Kubernetes命名空间名称

        Args:
            team_name: 团队名称
            project_name: 项目名称

        Returns:
            str: 命名空间名称（符合K8S命名规范）
        """
        import re

        # 合并团队和项目名称
        namespace = f"{team_name}-{project_name}"

        # 转换为小写
        namespace = namespace.lower()

        # 只保留字母、数字和连字符
        namespace = re.sub(r"[^a-z0-9-]", "-", namespace)

        # 移除连续的连字符
        namespace = re.sub(r"-+", "-", namespace)

        # 移除首尾的连字符
        namespace = namespace.strip("-")

        # 截断到63个字符（K8S限制）
        if len(namespace) > 63:
            namespace = namespace[:63].rstrip("-")

        return namespace
