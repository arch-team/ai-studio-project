"""Create resource_quotas table and add FK to users.

Revision ID: 002_create_resource_quotas
Revises: 001_create_users
Create Date: 2026-01-12

Task: T010 - 创建 resource_quotas 表迁移
字段: id, name, quota_type, max_cpu_cores, max_gpu_count, max_memory_gb, max_storage_gb
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "002_create_resource_quotas"
down_revision: Union[str, None] = "001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create resource_quotas table and add FK constraint to users."""
    op.create_table(
        "resource_quotas",
        sa.Column(
            "id",
            mysql.BIGINT(unsigned=True),
            autoincrement=True,
            nullable=False,
            comment="配额ID",
        ),
        sa.Column(
            "name",
            sa.String(128),
            nullable=False,
            comment="配额名称 (例如: team-a-quota)",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="配额描述",
        ),
        sa.Column(
            "quota_type",
            sa.Enum("user", "team", "project", name="quota_type"),
            nullable=False,
            server_default="user",
            comment="配额类型",
        ),
        # CPU 配额 (单位: vCPU)
        sa.Column(
            "max_cpu_cores",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            comment="最大 CPU 核心数",
        ),
        sa.Column(
            "reserved_cpu_cores",
            mysql.INTEGER(unsigned=True),
            nullable=True,
            server_default="0",
            comment="预留 CPU 核心数",
        ),
        # GPU 配额
        sa.Column(
            "max_gpu_count",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            comment="最大 GPU 数量",
        ),
        sa.Column(
            "reserved_gpu_count",
            mysql.INTEGER(unsigned=True),
            nullable=True,
            server_default="0",
            comment="预留 GPU 数量",
        ),
        sa.Column(
            "gpu_types",
            mysql.JSON(),
            nullable=True,
            comment='允许的 GPU 类型 (例如: ["ml.p4d.24xlarge", "ml.g5.xlarge"])',
        ),
        # 内存配额 (单位: GB)
        sa.Column(
            "max_memory_gb",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            comment="最大内存 (GB)",
        ),
        sa.Column(
            "reserved_memory_gb",
            mysql.INTEGER(unsigned=True),
            nullable=True,
            server_default="0",
            comment="预留内存 (GB)",
        ),
        # 存储配额 (单位: GB)
        sa.Column(
            "max_storage_gb",
            mysql.INTEGER(unsigned=True),
            nullable=True,
            comment="最大存储空间 (GB)",
        ),
        # 训练任务配额
        sa.Column(
            "max_concurrent_jobs",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="5",
            comment="最大并发训练任务数",
        ),
        sa.Column(
            "max_total_jobs",
            mysql.INTEGER(unsigned=True),
            nullable=True,
            comment="总训练任务数限制 (NULL 表示无限制)",
        ),
        # Spot 实例配额
        sa.Column(
            "max_spot_instances",
            mysql.INTEGER(unsigned=True),
            nullable=True,
            server_default="0",
            comment="最大 Spot 实例数",
        ),
        # 配额状态
        sa.Column(
            "status",
            sa.Enum("active", "suspended", "expired", name="quota_status"),
            nullable=False,
            server_default="active",
            comment="配额状态",
        ),
        # 有效期
        sa.Column(
            "valid_from",
            mysql.DATETIME(fsp=3),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(3)"),
            comment="生效时间",
        ),
        sa.Column(
            "valid_until",
            mysql.DATETIME(fsp=3),
            nullable=True,
            comment="过期时间 (NULL 表示永久)",
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
        sa.Column(
            "created_by",
            sa.String(36),
            nullable=True,
            comment="创建人用户ID (UUID)",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uk_resource_quotas_name"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_resource_quotas_created_by",
            ondelete="SET NULL",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="资源配额表",
    )

    # 创建索引
    op.create_index("idx_resource_quotas_quota_type", "resource_quotas", ["quota_type"])
    op.create_index("idx_resource_quotas_status", "resource_quotas", ["status"])
    op.create_index(
        "idx_resource_quotas_valid_period", "resource_quotas", ["valid_from", "valid_until"]
    )
    op.create_index("idx_resource_quotas_created_by", "resource_quotas", ["created_by"])

    # 添加 users 表的外键约束 (resource_quota_id -> resource_quotas.id)
    op.create_foreign_key(
        "fk_users_resource_quota_id",
        "users",
        "resource_quotas",
        ["resource_quota_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Drop resource_quotas table and remove FK from users."""
    # 先删除 users 表的外键约束
    op.drop_constraint("fk_users_resource_quota_id", "users", type_="foreignkey")

    # 删除索引
    op.drop_index("idx_resource_quotas_created_by", table_name="resource_quotas")
    op.drop_index("idx_resource_quotas_valid_period", table_name="resource_quotas")
    op.drop_index("idx_resource_quotas_status", table_name="resource_quotas")
    op.drop_index("idx_resource_quotas_quota_type", table_name="resource_quotas")

    op.drop_table("resource_quotas")
