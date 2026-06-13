"""add auth fields to users and create password_history, login_attempts tables

Revision ID: a743f443fb73
Revises: 7778e77de8a6
Create Date: 2026-01-14 22:54:26.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a743f443fb73"
down_revision: str | None = "7778e77de8a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add authentication fields to users table
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=True,
            comment="密码哈希(本地账号)",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_expires_at",
            sa.DateTime(timezone=False),
            nullable=True,
            comment="密码过期时间",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "locked_until",
            sa.DateTime(timezone=False),
            nullable=True,
            comment="账号锁定截止时间",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "failed_login_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="连续登录失败次数",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "auth_type",
            sa.Enum("sso", "local", name="authtype"),
            nullable=False,
            server_default="sso",
            comment="认证类型",
        ),
    )

    # 2. Create password_history table
    op.create_table(
        "password_history",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="记录ID",
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
            comment="用户ID",
        ),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            comment="密码哈希",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="创建时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_password_history_user_id",
            ondelete="CASCADE",
        ),
        comment="密码历史表",
    )
    op.create_index(
        "ix_password_history_user_id",
        "password_history",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_password_history_created_at",
        "password_history",
        ["created_at"],
        unique=False,
    )

    # 3. Create login_attempts table
    op.create_table(
        "login_attempts",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="记录ID",
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=True,
            comment="用户ID(NULL表示用户不存在)",
        ),
        sa.Column(
            "username",
            sa.String(length=64),
            nullable=False,
            comment="尝试的用户名",
        ),
        sa.Column(
            "ip_address",
            sa.String(length=45),
            nullable=False,
            comment="IP地址",
        ),
        sa.Column(
            "user_agent",
            sa.Text(),
            nullable=True,
            comment="User-Agent",
        ),
        sa.Column(
            "success",
            sa.Boolean(),
            nullable=False,
            server_default="0",
            comment="是否成功",
        ),
        sa.Column(
            "failure_reason",
            sa.String(length=50),
            nullable=True,
            comment="失败原因",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="尝试时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_login_attempts_user_id",
            ondelete="SET NULL",
        ),
        comment="登录尝试记录表",
    )
    op.create_index(
        "ix_login_attempts_user_id",
        "login_attempts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_login_attempts_username",
        "login_attempts",
        ["username"],
        unique=False,
    )
    op.create_index(
        "ix_login_attempts_ip_address",
        "login_attempts",
        ["ip_address"],
        unique=False,
    )
    op.create_index(
        "ix_login_attempts_created_at",
        "login_attempts",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_login_attempts_user_recent",
        "login_attempts",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop login_attempts table
    op.drop_index("ix_login_attempts_user_recent", table_name="login_attempts")
    op.drop_index("ix_login_attempts_created_at", table_name="login_attempts")
    op.drop_index("ix_login_attempts_ip_address", table_name="login_attempts")
    op.drop_index("ix_login_attempts_username", table_name="login_attempts")
    op.drop_index("ix_login_attempts_user_id", table_name="login_attempts")
    op.drop_table("login_attempts")

    # Drop password_history table
    op.drop_index("ix_password_history_created_at", table_name="password_history")
    op.drop_index("ix_password_history_user_id", table_name="password_history")
    op.drop_table("password_history")

    # Drop auth columns from users
    op.drop_column("users", "auth_type")
    op.drop_column("users", "failed_login_count")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "password_expires_at")
    op.drop_column("users", "password_hash")

    # Drop enum type
    sa.Enum(name="authtype").drop(op.get_bind(), checkfirst=True)
