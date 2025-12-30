"""SQLAlchemy基础模型

提供所有模型的公共字段和方法
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类

    提供公共字段：
    - id: 主键
    - created_at: 创建时间
    - updated_at: 更新时间
    """

    # 自动生成表名（类名转snake_case）
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """自动生成表名

        将类名从CamelCase转换为snake_case
        例如: UserProfile -> user_profile
        """
        import re

        name = cls.__name__
        # 在大写字母前插入下划线
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        # 处理连续的大写字母
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    # 主键ID
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    # 时间戳字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )

    def to_dict(self) -> dict[str, Any]:
        """将模型转换为字典

        Returns:
            dict: 模型的字典表示
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # 处理datetime对象
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def __repr__(self) -> str:
        """模型的字符串表示

        Returns:
            str: 模型信息
        """
        class_name = self.__class__.__name__
        attrs = ", ".join(
            f"{key}={value!r}"
            for key, value in self.to_dict().items()
            if key in ["id", "name", "email", "username"]  # 只显示关键字段
        )
        return f"{class_name}({attrs})"


class TimestampMixin:
    """时间戳Mixin

    为不需要Base完整功能的模型提供时间戳字段
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class SoftDeleteMixin:
    """软删除Mixin

    为模型提供软删除功能
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="删除时间",
    )

    @property
    def is_deleted(self) -> bool:
        """是否已删除

        Returns:
            bool: True表示已删除
        """
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """软删除记录"""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """恢复已删除的记录"""
        self.deleted_at = None


__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
]
