"""Create users table.

Revision ID: 001_create_users
Revises:
Create Date: 2026-01-12

Task: T009 - 创建 users 表迁移
字段: id (UUID), username, email, iam_identity_id, role (enum), status, resource_quota_id (FK)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "001_create_users"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table."""
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.String(36),
            nullable=False,
            comment="用户ID (UUID)",
        ),
        sa.Column(
            "username",
            sa.String(64),
            nullable=False,
            comment="用户名 (IAM 用户名)",
        ),
        sa.Column(
            "email",
            sa.String(255),
            nullable=False,
            comment="邮箱地址",
        ),
        sa.Column(
            "display_name",
            sa.String(128),
            nullable=True,
            comment="显示名称",
        ),
        sa.Column(
            "iam_identity_id",
            sa.String(255),
            nullable=True,
            comment="AWS IAM Identity Center 用户ID",
        ),
        sa.Column(
            "iam_groups",
            mysql.JSON(),
            nullable=True,
            comment="IAM 用户组列表 (JSON 数组)",
        ),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", "suspended", name="user_status"),
            nullable=False,
            server_default="active",
            comment="用户状态",
        ),
        sa.Column(
            "role",
            sa.Enum("admin", "project_manager", "engineer", "viewer", name="user_role"),
            nullable=False,
            server_default="engineer",
            comment="用户角色",
        ),
        sa.Column(
            "resource_quota_id",
            mysql.BIGINT(unsigned=True),
            nullable=True,
            comment="关联的资源配额ID",
        ),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=3),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(3)"),
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=3),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)"),
            comment="更新时间",
        ),
        sa.Column(
            "last_login_at",
            mysql.DATETIME(fsp=3),
            nullable=True,
            comment="最后登录时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uk_users_username"),
        sa.UniqueConstraint("email", name="uk_users_email"),
        sa.UniqueConstraint("iam_identity_id", name="uk_users_iam_identity_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="用户表",
    )

    # 创建索引
    op.create_index("idx_users_status", "users", ["status"])
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_resource_quota_id", "users", ["resource_quota_id"])
    op.create_index("idx_users_created_at", "users", ["created_at"])


def downgrade() -> None:
    """Drop users table."""
    op.drop_index("idx_users_created_at", table_name="users")
    op.drop_index("idx_users_resource_quota_id", table_name="users")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_index("idx_users_status", table_name="users")
    op.drop_table("users")
