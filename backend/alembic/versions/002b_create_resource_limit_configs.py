"""Create resource_limit_configs table.

Revision ID: 002b_create_resource_limit_configs
Revises: 002_create_resource_quotas
Create Date: 2026-01-12

Task: T010b - 创建 resource_limit_configs 表迁移
字段: id, config_name, role (enum: admin/project_manager/engineer/viewer), project_id (FK, nullable),
      max_gpu_per_job, max_cpu_per_job, max_memory_gb_per_job, max_storage_gb_per_job,
      max_nodes_per_job, priority_default (enum: high/medium/low), created_at, updated_at
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "002b_create_resource_limit_configs"
down_revision: Union[str, None] = "002_create_resource_quotas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create resource_limit_configs table."""
    op.create_table(
        "resource_limit_configs",
        sa.Column(
            "id",
            mysql.BIGINT(unsigned=True),
            autoincrement=True,
            nullable=False,
            comment="配置ID",
        ),
        sa.Column(
            "config_name",
            sa.String(128),
            nullable=False,
            comment="配置名称",
        ),
        sa.Column(
            "role",
            sa.Enum("admin", "project_manager", "engineer", "viewer", name="limit_config_role"),
            nullable=False,
            comment="适用角色",
        ),
        sa.Column(
            "project_id",
            mysql.BIGINT(unsigned=True),
            nullable=True,
            comment="项目ID (NULL 表示全局配置)",
        ),
        # 单任务资源限制
        sa.Column(
            "max_gpu_per_job",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="8",
            comment="单任务最大 GPU 数量",
        ),
        sa.Column(
            "max_cpu_per_job",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="64",
            comment="单任务最大 CPU 核心数",
        ),
        sa.Column(
            "max_memory_gb_per_job",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="512",
            comment="单任务最大内存 (GB)",
        ),
        sa.Column(
            "max_storage_gb_per_job",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="1000",
            comment="单任务最大存储 (GB)",
        ),
        sa.Column(
            "max_nodes_per_job",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="4",
            comment="单任务最大节点数",
        ),
        # 默认优先级
        sa.Column(
            "priority_default",
            sa.Enum("high", "medium", "low", name="priority_level"),
            nullable=False,
            server_default="medium",
            comment="默认任务优先级",
        ),
        # 审计字段
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role", "project_id", name="uk_resource_limit_configs_role_project"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="资源限制配置表",
    )

    # 创建索引
    op.create_index("idx_resource_limit_configs_role", "resource_limit_configs", ["role"])
    op.create_index("idx_resource_limit_configs_project_id", "resource_limit_configs", ["project_id"])
    op.create_index("idx_resource_limit_configs_created_at", "resource_limit_configs", ["created_at"])


def downgrade() -> None:
    """Drop resource_limit_configs table."""
    op.drop_index("idx_resource_limit_configs_created_at", table_name="resource_limit_configs")
    op.drop_index("idx_resource_limit_configs_project_id", table_name="resource_limit_configs")
    op.drop_index("idx_resource_limit_configs_role", table_name="resource_limit_configs")
    op.drop_table("resource_limit_configs")
