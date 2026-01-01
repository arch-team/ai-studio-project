"""团队模型

管理团队信息和成员
"""

from typing import TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin

if TYPE_CHECKING:
    from models.user.user import User
    from models.user.project import Project

# 团队成员关联表
team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Team(Base, SoftDeleteMixin):
    """团队模型

    Attributes:
        name: 团队名称（唯一）
        description: 团队描述
        owner_id: 团队所有者ID
        owner: 团队所有者
        members: 团队成员列表
        projects: 团队项目列表
    """

    __tablename__ = "teams"

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False, comment="团队名称"
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="团队描述")

    # 所有者
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所有者ID"
    )

    # 关系
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])

    members: Mapped[list["User"]] = relationship(
        "User", secondary=team_members
    )

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="team")

    def __repr__(self) -> str:
        return f"Team(id={self.id}, name={self.name!r}, owner_id={self.owner_id})"

    @property
    def member_count(self) -> int:
        """团队成员数量

        Returns:
            int: 成员数量
        """
        return len(self.members) if self.members else 0

    @property
    def project_count(self) -> int:
        """团队项目数量

        Returns:
            int: 项目数量
        """
        return len(self.projects) if self.projects else 0

    def is_member(self, user_id: int) -> bool:
        """检查用户是否为团队成员

        Args:
            user_id: 用户ID

        Returns:
            bool: True表示是成员
        """
        if not self.members:
            return False
        return any(member.id == user_id for member in self.members)

    def is_owner(self, user_id: int) -> bool:
        """检查用户是否为团队所有者

        Args:
            user_id: 用户ID

        Returns:
            bool: True表示是所有者
        """
        return self.owner_id == user_id
