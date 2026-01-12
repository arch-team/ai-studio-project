"""Create development_spaces table.

Revision ID: 004_create_development_spaces
Revises: 003_create_audit_logs
Create Date: 2026-01-12

Task: T010c - 创建 development_spaces 表迁移
字段: id (UUID), space_name (VARCHAR 255), owner_id (FK users),
      instance_type (enum: ml.t3.medium/ml.t3.large/ml.g4dn.xlarge),
      space_type (enum: jupyter/vscode/rstudio),
      status (enum: pending/running/stopped/failed/deleted),
      storage_size_gb (INT), lifecycle_config_arn (VARCHAR),
      sagemaker_space_arn (VARCHAR), created_at (TIMESTAMP),
      updated_at (TIMESTAMP), deleted_at (TIMESTAMP, nullable)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "004_create_development_spaces"
down_revision: Union[str, None] = "003_create_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create development_spaces table."""
    op.create_table(
        "development_spaces",
        # 主键 (使用 UUID)
        sa.Column(
            "id",
            sa.CHAR(36),
            nullable=False,
            comment="Space ID (UUID)",
        ),
        # Space 标识
        sa.Column(
            "space_name",
            sa.String(255),
            nullable=False,
            comment="Space 名称",
        ),
        # 所有者
        sa.Column(
            "owner_id",
            sa.String(36),
            nullable=False,
            comment="所有者用户ID (UUID)",
        ),
        # 实例配置 (基于 spec.md User Story 5 资源配额定义)
        sa.Column(
            "instance_type",
            sa.Enum(
                "ml.t3.medium",
                "ml.t3.large",
                "ml.g4dn.xlarge",
                "ml.g5.xlarge",
                "ml.g5.2xlarge",
                name="space_instance_type",
            ),
            nullable=False,
            server_default="ml.g5.xlarge",
            comment="实例类型",
        ),
        # Space 类型
        sa.Column(
            "space_type",
            sa.Enum("jupyter", "vscode", "rstudio", name="space_type"),
            nullable=False,
            server_default="jupyter",
            comment="Space 类型",
        ),
        # Space 状态 (对应 SageMaker Space 状态)
        sa.Column(
            "status",
            sa.Enum("pending", "running", "stopped", "failed", "deleted", name="space_status"),
            nullable=False,
            server_default="pending",
            comment="Space 状态",
        ),
        # 存储配置
        sa.Column(
            "storage_size_gb",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="50",
            comment="存储大小 (GB)",
        ),
        # SageMaker 集成
        sa.Column(
            "lifecycle_config_arn",
            sa.String(512),
            nullable=True,
            comment="Lifecycle 配置 ARN",
        ),
        sa.Column(
            "sagemaker_space_arn",
            sa.String(512),
            nullable=True,
            comment="SageMaker Space ARN",
        ),
        sa.Column(
            "studio_url",
            sa.String(1024),
            nullable=True,
            comment="SageMaker Studio URL",
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
            "deleted_at",
            mysql.DATETIME(fsp=3),
            nullable=True,
            comment="删除时间 (软删除)",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("space_name", "deleted_at", name="uk_development_spaces_name_not_deleted"),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_development_spaces_owner_id",
            ondelete="CASCADE",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="开发空间表",
    )

    # 创建索引
    op.create_index("idx_development_spaces_owner_id", "development_spaces", ["owner_id"])
    op.create_index("idx_development_spaces_status", "development_spaces", ["status"])
    op.create_index("idx_development_spaces_space_type", "development_spaces", ["space_type"])
    op.create_index("idx_development_spaces_instance_type", "development_spaces", ["instance_type"])
    op.create_index("idx_development_spaces_created_at", "development_spaces", ["created_at"])
    op.create_index("idx_development_spaces_deleted_at", "development_spaces", ["deleted_at"])


def downgrade() -> None:
    """Drop development_spaces table."""
    op.drop_index("idx_development_spaces_deleted_at", table_name="development_spaces")
    op.drop_index("idx_development_spaces_created_at", table_name="development_spaces")
    op.drop_index("idx_development_spaces_instance_type", table_name="development_spaces")
    op.drop_index("idx_development_spaces_space_type", table_name="development_spaces")
    op.drop_index("idx_development_spaces_status", table_name="development_spaces")
    op.drop_index("idx_development_spaces_owner_id", table_name="development_spaces")
    op.drop_table("development_spaces")
