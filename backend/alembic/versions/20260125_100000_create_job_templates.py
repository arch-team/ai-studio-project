"""create job_templates table

Revision ID: 8f2g3h4i5j6k
Revises: 7e1f2g5h4i6j
Create Date: 2026-01-25 10:00:00.000000

Creates the job_templates table for storing reusable training job templates.
Templates allow users to save and share common training configurations.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "8f2g3h4i5j6k"
down_revision: Union[str, None] = "7e1f2g5h4i6j"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create job_templates table
    op.create_table(
        "job_templates",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="模板ID",
        ),
        # Template identification
        sa.Column(
            "name",
            sa.String(length=128),
            nullable=False,
            comment="模板名称",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="模板描述",
        ),
        # Owner
        sa.Column(
            "owner_id",
            sa.BigInteger(),
            nullable=False,
            comment="所有者用户ID",
        ),
        # Visibility
        sa.Column(
            "visibility",
            sa.Enum("PRIVATE", "TEAM", "PUBLIC", name="templatevisibility"),
            nullable=False,
            server_default="PRIVATE",
            comment="可见性范围: PRIVATE=仅自己, TEAM=团队, PUBLIC=所有人",
        ),
        # Training configuration (JSON blob)
        sa.Column(
            "training_config",
            mysql.JSON(),
            nullable=False,
            comment="训练配置 (JSON): image, instance_type, instance_count, distribution_strategy, environment 等",
        ),
        # Usage statistics
        sa.Column(
            "usage_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="使用次数",
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(),
            nullable=True,
            comment="最后使用时间",
        ),
        # Audit fields
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
            comment="更新时间",
        ),
        # Soft delete
        sa.Column(
            "deleted_at",
            sa.DateTime(),
            nullable=True,
            comment="软删除时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_job_templates_owner_id",
            ondelete="CASCADE",
        ),
        comment="任务模板表",
    )

    # Create indexes
    op.create_index(
        "ix_job_templates_owner_id",
        "job_templates",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        "ix_job_templates_visibility",
        "job_templates",
        ["visibility"],
        unique=False,
    )
    op.create_index(
        "ix_job_templates_name",
        "job_templates",
        ["name"],
        unique=False,
    )
    op.create_index(
        "ix_job_templates_usage_count",
        "job_templates",
        ["usage_count"],
        unique=False,
    )
    op.create_index(
        "ix_job_templates_deleted_at",
        "job_templates",
        ["deleted_at"],
        unique=False,
    )
    # Composite index for listing visible templates (owner + visibility + deleted)
    op.create_index(
        "ix_job_templates_owner_visibility_deleted",
        "job_templates",
        ["owner_id", "visibility", "deleted_at"],
        unique=False,
    )
    # Composite index for popular templates query
    op.create_index(
        "ix_job_templates_visibility_usage_deleted",
        "job_templates",
        ["visibility", "usage_count", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_job_templates_visibility_usage_deleted", table_name="job_templates")
    op.drop_index("ix_job_templates_owner_visibility_deleted", table_name="job_templates")
    op.drop_index("ix_job_templates_deleted_at", table_name="job_templates")
    op.drop_index("ix_job_templates_usage_count", table_name="job_templates")
    op.drop_index("ix_job_templates_name", table_name="job_templates")
    op.drop_index("ix_job_templates_visibility", table_name="job_templates")
    op.drop_index("ix_job_templates_owner_id", table_name="job_templates")

    # Drop table
    op.drop_table("job_templates")

    # Drop enum type
    sa.Enum(name="templatevisibility").drop(op.get_bind(), checkfirst=True)
