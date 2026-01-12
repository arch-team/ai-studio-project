"""Create audit_logs table.

Revision ID: 003_create_audit_logs
Revises: 002b_create_resource_limit_configs
Create Date: 2026-01-12

Task: T010a - 创建 audit_logs 表迁移
字段: id, user_id (FK), operation_type (enum: create/update/delete/login/logout),
      resource_type (enum: training_job/dataset/model/user/quota/space),
      resource_id, request_data (JSON), response_data (JSON), ip_address,
      user_agent, status (enum: success/failed), created_at, expires_at (created_at + 90天)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "003_create_audit_logs"
down_revision: Union[str, None] = "002b_create_resource_limit_configs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_logs table."""
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            mysql.BIGINT(unsigned=True),
            autoincrement=True,
            nullable=False,
            comment="审计日志ID",
        ),
        # 用户关联
        sa.Column(
            "user_id",
            sa.String(36),
            nullable=False,
            comment="操作用户ID (UUID)",
        ),
        # 操作信息
        sa.Column(
            "operation_type",
            sa.Enum("create", "update", "delete", "login", "logout", name="audit_operation_type"),
            nullable=False,
            comment="操作类型",
        ),
        sa.Column(
            "resource_type",
            sa.Enum(
                "training_job",
                "dataset",
                "model",
                "user",
                "quota",
                "space",
                "checkpoint",
                name="audit_resource_type",
            ),
            nullable=False,
            comment="资源类型",
        ),
        sa.Column(
            "resource_id",
            sa.String(128),
            nullable=True,
            comment="资源ID (字符串类型，支持 UUID 和数字 ID)",
        ),
        # 请求/响应数据
        sa.Column(
            "request_data",
            mysql.JSON(),
            nullable=True,
            comment="请求数据 (JSON)",
        ),
        sa.Column(
            "response_data",
            mysql.JSON(),
            nullable=True,
            comment="响应数据 (JSON)",
        ),
        # 客户端信息
        sa.Column(
            "ip_address",
            sa.String(45),
            nullable=True,
            comment="客户端 IP 地址 (支持 IPv6)",
        ),
        sa.Column(
            "user_agent",
            sa.String(512),
            nullable=True,
            comment="用户代理字符串",
        ),
        # 操作状态
        sa.Column(
            "status",
            sa.Enum("success", "failed", name="audit_status"),
            nullable=False,
            server_default="success",
            comment="操作状态",
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="错误信息 (仅当 status=failed 时)",
        ),
        # 时间戳
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=3),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(3)"),
            comment="创建时间",
        ),
        # 过期时间 (使用生成列，默认 90 天后过期)
        # 注意: MySQL 8.0+ 支持 STORED 生成列
        sa.Column(
            "expires_at",
            mysql.DATETIME(fsp=3),
            sa.Computed("DATE_ADD(created_at, INTERVAL 90 DAY)", persisted=True),
            comment="过期时间 (created_at + 90天)",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_audit_logs_user_id",
            ondelete="CASCADE",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="审计日志表",
    )

    # 创建索引
    op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_operation_type", "audit_logs", ["operation_type"])
    op.create_index("idx_audit_logs_resource_type", "audit_logs", ["resource_type"])
    op.create_index("idx_audit_logs_resource_id", "audit_logs", ["resource_id"])
    op.create_index("idx_audit_logs_status", "audit_logs", ["status"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("idx_audit_logs_expires_at", "audit_logs", ["expires_at"])
    # 复合索引 (常见查询模式)
    op.create_index(
        "idx_audit_logs_user_operation_created",
        "audit_logs",
        ["user_id", "operation_type", "created_at"],
    )
    op.create_index(
        "idx_audit_logs_resource_type_id",
        "audit_logs",
        ["resource_type", "resource_id"],
    )


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_index("idx_audit_logs_resource_type_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_user_operation_created", table_name="audit_logs")
    op.drop_index("idx_audit_logs_expires_at", table_name="audit_logs")
    op.drop_index("idx_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("idx_audit_logs_status", table_name="audit_logs")
    op.drop_index("idx_audit_logs_resource_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("idx_audit_logs_operation_type", table_name="audit_logs")
    op.drop_index("idx_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
