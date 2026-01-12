"""AuditLog model - SQLAlchemy 2.0 async model.

Task: T012a - 创建 AuditLog 模型
支持审计日志记录,包含操作类型、资源类型、请求/响应数据等
90 天自动过期 (通过数据库生成列实现)
"""

from datetime import datetime, timedelta
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import BIGINT, JSON  # BIGINT still used for audit_log.id
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class AuditOperationType(str, PyEnum):
    """审计操作类型枚举."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"


class AuditResourceType(str, PyEnum):
    """审计资源类型枚举."""

    TRAINING_JOB = "training_job"
    DATASET = "dataset"
    MODEL = "model"
    USER = "user"
    QUOTA = "quota"
    SPACE = "space"
    CHECKPOINT = "checkpoint"


class AuditStatus(str, PyEnum):
    """审计操作状态枚举."""

    SUCCESS = "success"
    FAILED = "failed"


class AuditLog(Base):
    """审计日志模型 - 记录系统操作日志,支持 90 天自动过期."""

    __tablename__ = "audit_logs"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
        "comment": "审计日志表",
    }

    # 主键
    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="审计日志ID",
    )

    # 用户关联
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="操作用户ID (UUID)",
    )

    # 操作信息
    operation_type: Mapped[AuditOperationType] = mapped_column(
        Enum(AuditOperationType, name="audit_operation_type"),
        nullable=False,
        comment="操作类型",
    )
    resource_type: Mapped[AuditResourceType] = mapped_column(
        Enum(AuditResourceType, name="audit_resource_type"),
        nullable=False,
        comment="资源类型",
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="资源ID (字符串类型，支持 UUID 和数字 ID)",
    )

    # 请求/响应数据
    request_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="请求数据 (JSON)",
    )
    response_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="响应数据 (JSON)",
    )

    # 客户端信息
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="客户端 IP 地址 (支持 IPv6)",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="用户代理字符串",
    )

    # 操作状态
    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus, name="audit_status"),
        nullable=False,
        default=AuditStatus.SUCCESS,
        comment="操作状态",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息 (仅当 status=failed 时)",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    # 注意: expires_at 是数据库生成列,在 Python 模型中不设置默认值
    # 数据库会自动计算: DATE_ADD(created_at, INTERVAL 90 DAY)

    # 关联关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[user_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"op={self.operation_type.value}, res={self.resource_type.value})>"
        )

    @property
    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.status == AuditStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """Check if operation failed."""
        return self.status == AuditStatus.FAILED

    @property
    def expires_at_calculated(self) -> datetime:
        """Calculate expiration time (90 days from creation).

        Note: This is a fallback calculation. The actual expires_at
        is computed by the database as a generated column.
        """
        return self.created_at + timedelta(days=90)

    @classmethod
    def create_log(
        cls,
        user_id: str,
        operation_type: AuditOperationType,
        resource_type: AuditResourceType,
        resource_id: Optional[str] = None,
        request_data: Optional[dict[str, Any]] = None,
        response_data: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: AuditStatus = AuditStatus.SUCCESS,
        error_message: Optional[str] = None,
    ) -> "AuditLog":
        """Factory method to create an audit log entry.

        Args:
            user_id: The ID of the user performing the operation
            operation_type: Type of operation (create/update/delete/login/logout)
            resource_type: Type of resource being operated on
            resource_id: Optional ID of the resource
            request_data: Optional request payload
            response_data: Optional response payload
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            status: Operation status (success/failed)
            error_message: Optional error message for failed operations

        Returns:
            AuditLog instance ready for database insertion
        """
        return cls(
            user_id=user_id,
            operation_type=operation_type,
            resource_type=resource_type,
            resource_id=resource_id,
            request_data=request_data,
            response_data=response_data,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )
