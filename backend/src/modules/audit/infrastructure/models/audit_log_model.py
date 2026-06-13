"""审计日志 ORM 模型."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, event, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.modules.audit.domain.value_objects import AuditStatus, OperationType, ResourceType
from src.shared.infrastructure import Base, lowercase_enum
from src.shared.utils import utc_now


class AuditLogModel(Base):
    """审计日志 ORM 模型."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="审计日志ID",
    )

    # 用户关联
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="用户ID",
    )

    # 操作详情
    operation_type: Mapped[OperationType] = mapped_column(
        lowercase_enum(OperationType),
        nullable=False,
        index=True,
        comment="操作类型",
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        lowercase_enum(ResourceType),
        nullable=False,
        index=True,
        comment="资源类型",
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="资源ID",
    )

    # 请求/响应数据
    request_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="请求数据",
    )
    response_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="响应数据",
    )

    # 客户端信息
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IP地址",
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="User-Agent",
    )

    # 操作状态
    status: Mapped[AuditStatus] = mapped_column(
        lowercase_enum(AuditStatus),
        nullable=False,
        default=AuditStatus.SUCCESS,
        index=True,
        comment="操作状态",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="创建时间",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        index=True,
        comment="过期时间(90天后)",
    )

    # 关联关系 - auth 模块迁移后配置

    __table_args__ = ({"comment": "审计日志表"},)


@event.listens_for(AuditLogModel, "before_insert")
def set_expires_at(mapper: Any, connection: Any, target: AuditLogModel) -> None:
    """自动设置 expires_at 为创建后 90 天."""
    if target.expires_at is None:
        target.expires_at = utc_now() + timedelta(days=90)
