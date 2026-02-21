"""create upload_sessions table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-26 10:01:00.000000

Creates the upload_sessions table for tracking S3 multipart upload progress,
supporting cross-session resume for large file uploads.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create upload_sessions table
    op.create_table(
        "upload_sessions",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="上传会话ID",
        ),
        # Upload identification
        sa.Column(
            "upload_id",
            sa.String(length=128),
            nullable=False,
            comment="S3 Multipart Upload ID",
        ),
        sa.Column(
            "dataset_id",
            sa.BigInteger(),
            nullable=False,
            comment="关联数据集ID",
        ),
        # S3 storage info
        sa.Column(
            "bucket",
            sa.String(length=128),
            nullable=False,
            comment="S3 桶名",
        ),
        sa.Column(
            "s3_key",
            sa.String(length=512),
            nullable=False,
            comment="S3 对象键",
        ),
        # File info
        sa.Column(
            "filename",
            sa.String(length=256),
            nullable=False,
            comment="原始文件名",
        ),
        sa.Column(
            "content_type",
            sa.String(length=128),
            nullable=False,
            server_default="application/octet-stream",
            comment="MIME 类型",
        ),
        sa.Column(
            "total_size",
            sa.BigInteger(),
            nullable=False,
            comment="文件总大小 (字节)",
        ),
        sa.Column(
            "part_size",
            sa.Integer(),
            nullable=False,
            comment="分片大小 (字节)",
        ),
        # Status
        sa.Column(
            "status",
            sa.Enum(
                "INITIATED", "IN_PROGRESS", "COMPLETING", "COMPLETED", "ABORTED", "FAILED",
                name="uploadsessionstatus"
            ),
            nullable=False,
            server_default="INITIATED",
            comment="上传状态",
        ),
        # Part tracking (JSON array)
        sa.Column(
            "completed_parts",
            mysql.JSON(),
            nullable=True,
            comment='已完成分片列表 (JSON 数组)',
        ),
        # Progress statistics
        sa.Column(
            "uploaded_bytes",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
            comment="已上传字节数",
        ),
        sa.Column(
            "completed_part_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="已完成分片数",
        ),
        # Owner
        sa.Column(
            "owner_id",
            sa.BigInteger(),
            nullable=False,
            comment="上传者用户ID",
        ),
        # Timestamps
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
            "expires_at",
            sa.DateTime(),
            nullable=True,
            comment="会话过期时间 (7天后自动清理)",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name="fk_upload_sessions_dataset_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_upload_sessions_owner_id",
            ondelete="CASCADE",
        ),
        comment="数据集上传会话表",
    )

    # Create unique constraint for upload_id
    op.create_unique_constraint(
        "uk_upload_sessions_upload_id",
        "upload_sessions",
        ["upload_id"],
    )

    # Create indexes
    op.create_index(
        "ix_upload_sessions_dataset_id",
        "upload_sessions",
        ["dataset_id"],
        unique=False,
    )
    op.create_index(
        "ix_upload_sessions_owner_id",
        "upload_sessions",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        "ix_upload_sessions_status",
        "upload_sessions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_upload_sessions_expires_at",
        "upload_sessions",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop table (MySQL automatically drops all indexes and constraints)
    op.drop_table("upload_sessions")

    # Drop enum type
    sa.Enum(name="uploadsessionstatus").drop(op.get_bind(), checkfirst=True)
