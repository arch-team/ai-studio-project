"""Login Attempt ORM model - Track authentication attempts for security auditing."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.infrastructure.persistence.models.user_model import UserModel


class LoginAttemptModel(Base):
    """Login attempt ORM model for tracking authentication attempts."""

    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="记录ID",
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="用户ID(NULL表示用户不存在)",
    )
    username: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="尝试的用户名",
    )
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        index=True,
        comment="IP地址",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User-Agent",
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="是否成功",
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="失败原因",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True,
        comment="尝试时间",
    )

    # Relationships
    user: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        back_populates="login_attempts",
    )

    __table_args__ = ({"comment": "登录尝试记录表"},)
