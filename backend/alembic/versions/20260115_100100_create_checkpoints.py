"""create checkpoints table

Revision ID: 5c9d0e3f2a4b
Revises: 4b8c9d2e1f3a
Create Date: 2026-01-15 10:01:00.000000

Creates the checkpoints table for storing training checkpoint metadata.
Backend scans FSx for Lustre storage to generate checkpoint records.
Supports tiered storage: NVMe -> FSx -> S3.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c9d0e3f2a4b"
down_revision: str | None = "4b8c9d2e1f3a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create checkpoints table
    op.create_table(
        "checkpoints",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="检查点ID",
        ),
        # Associated training job
        sa.Column(
            "training_job_id",
            sa.BigInteger(),
            nullable=False,
            comment="关联训练任务ID",
        ),
        # Checkpoint identification
        sa.Column(
            "checkpoint_name",
            sa.String(length=256),
            nullable=False,
            comment="检查点名称 (例如: checkpoint-epoch100.pth)",
        ),
        sa.Column(
            "storage_path",
            sa.String(length=512),
            nullable=False,
            comment="存储路径 (例如: /fsx/checkpoints/job-123/checkpoint-epoch100.pth)",
        ),
        # Checkpoint type
        sa.Column(
            "checkpoint_type",
            sa.Enum("EPOCH", "STEP", "BEST", "FINAL", "MANUAL", name="checkpointtype"),
            nullable=False,
            server_default="EPOCH",
            comment="检查点类型",
        ),
        # Training progress
        sa.Column(
            "epoch",
            sa.Integer(),
            nullable=True,
            comment="训练轮次",
        ),
        sa.Column(
            "step",
            sa.BigInteger(),
            nullable=True,
            comment="训练步数",
        ),
        # Checkpoint statistics
        sa.Column(
            "size_bytes",
            sa.BigInteger(),
            nullable=False,
            comment="文件大小 (字节)",
        ),
        # Checksum for integrity verification
        sa.Column(
            "checksum",
            sa.String(length=64),
            nullable=True,
            comment="SHA-256 校验和",
        ),
        # Training metrics at checkpoint save time
        sa.Column(
            "loss",
            sa.DECIMAL(precision=10, scale=6),
            nullable=True,
            comment="损失值",
        ),
        sa.Column(
            "accuracy",
            sa.DECIMAL(precision=5, scale=4),
            nullable=True,
            comment="准确率",
        ),
        sa.Column(
            "metrics",
            mysql.JSON(),
            nullable=True,
            comment="其他指标 (JSON 对象)",
        ),
        # Storage tier (tiered storage: NVMe -> FSx -> S3)
        sa.Column(
            "storage_tier",
            sa.Enum("NVME", "FSX", "S3", name="storagetier"),
            nullable=False,
            server_default="FSX",
            comment="存储层级",
        ),
        # Checkpoint status
        sa.Column(
            "status",
            sa.Enum("AVAILABLE", "ARCHIVED", "DELETED", name="checkpointstatus"),
            nullable=False,
            server_default="AVAILABLE",
            comment="检查点状态",
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
        sa.Column(
            "archived_at",
            sa.DateTime(),
            nullable=True,
            comment="归档时间 (S3)",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(),
            nullable=True,
            comment="删除时间 (软删除)",
        ),
        sa.PrimaryKeyConstraint("id"),
        # Unique constraint: same job cannot have duplicate checkpoint names
        sa.UniqueConstraint(
            "training_job_id",
            "checkpoint_name",
            name="uk_checkpoints_job_name",
        ),
        sa.ForeignKeyConstraint(
            ["training_job_id"],
            ["training_jobs.id"],
            name="fk_checkpoints_training_job_id",
            ondelete="CASCADE",
        ),
        comment="检查点表",
    )

    # Create indexes
    op.create_index(
        "ix_checkpoints_training_job_id",
        "checkpoints",
        ["training_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_checkpoints_checkpoint_type",
        "checkpoints",
        ["checkpoint_type"],
        unique=False,
    )
    op.create_index(
        "ix_checkpoints_storage_tier",
        "checkpoints",
        ["storage_tier"],
        unique=False,
    )
    op.create_index(
        "ix_checkpoints_status",
        "checkpoints",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_checkpoints_epoch",
        "checkpoints",
        ["epoch"],
        unique=False,
    )
    op.create_index(
        "ix_checkpoints_created_at",
        "checkpoints",
        ["created_at"],
        unique=False,
    )
    # Composite index for job + status + epoch queries
    op.create_index(
        "ix_checkpoints_job_status_epoch",
        "checkpoints",
        ["training_job_id", "status", "epoch"],
        unique=False,
    )
    # Composite index for job + status + created_at queries (for tiered migration)
    op.create_index(
        "ix_checkpoints_job_status_created",
        "checkpoints",
        ["training_job_id", "status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_checkpoints_job_status_created", table_name="checkpoints")
    op.drop_index("ix_checkpoints_job_status_epoch", table_name="checkpoints")
    op.drop_index("ix_checkpoints_created_at", table_name="checkpoints")
    op.drop_index("ix_checkpoints_epoch", table_name="checkpoints")
    op.drop_index("ix_checkpoints_status", table_name="checkpoints")
    op.drop_index("ix_checkpoints_storage_tier", table_name="checkpoints")
    op.drop_index("ix_checkpoints_checkpoint_type", table_name="checkpoints")
    op.drop_index("ix_checkpoints_training_job_id", table_name="checkpoints")

    # Drop table
    op.drop_table("checkpoints")

    # Drop enum types
    sa.Enum(name="checkpointstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="storagetier").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="checkpointtype").drop(op.get_bind(), checkfirst=True)
