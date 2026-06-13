"""create datasets table

Revision ID: 9a1b2c3d4e5f
Revises: 8f2g3h4i5j6k
Create Date: 2026-01-25 10:01:00.000000

Creates the datasets table for storing training data set metadata,
supporting FSx for Lustre, S3, and EFS storage backends.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a1b2c3d4e5f"
down_revision: str | None = "8f2g3h4i5j6k"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create datasets table
    op.create_table(
        "datasets",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="数据集ID",
        ),
        # Dataset identification
        sa.Column(
            "name",
            sa.String(length=128),
            nullable=False,
            comment="数据集名称",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="数据集描述",
        ),
        sa.Column(
            "version",
            sa.String(length=32),
            nullable=False,
            server_default="v1",
            comment="数据集版本",
        ),
        # Storage location
        sa.Column(
            "storage_type",
            sa.Enum("FSX", "S3", "EFS", name="datasetstoragetype"),
            nullable=False,
            server_default="FSX",
            comment="存储类型: FSX=FSx for Lustre, S3=S3, EFS=EFS",
        ),
        sa.Column(
            "storage_uri",
            sa.String(length=512),
            nullable=False,
            comment="存储 URI (例如: s3://bucket/path 或 /fsx/datasets/imagenet)",
        ),
        # Dataset statistics
        sa.Column(
            "total_size_bytes",
            sa.BigInteger(),
            nullable=True,
            comment="总大小 (字节)",
        ),
        sa.Column(
            "file_count",
            sa.Integer(),
            nullable=True,
            comment="文件数量",
        ),
        # Dataset type
        sa.Column(
            "dataset_type",
            sa.Enum("IMAGE", "TEXT", "AUDIO", "VIDEO", "TABULAR", "CUSTOM", name="datasettype"),
            nullable=False,
            comment="数据集类型: IMAGE=图像, TEXT=文本, AUDIO=音频, VIDEO=视频, TABULAR=表格, CUSTOM=自定义",
        ),
        sa.Column(
            "data_format",
            sa.String(length=64),
            nullable=True,
            comment="数据格式 (例如: imagenet, coco, csv, parquet)",
        ),
        # Dataset tags
        sa.Column(
            "tags",
            mysql.JSON(),
            nullable=True,
            comment='数据集标签 (JSON 数组,例如: ["cv", "classification", "imagenet"])',
        ),
        # Access permissions
        sa.Column(
            "visibility",
            sa.Enum("PUBLIC", "PRIVATE", "RESTRICTED", name="datasetvisibility"),
            nullable=False,
            server_default="PRIVATE",
            comment="可见性: PUBLIC=公开, PRIVATE=私有, RESTRICTED=受限",
        ),
        sa.Column(
            "owner_id",
            sa.BigInteger(),
            nullable=False,
            comment="所有者用户ID",
        ),
        # Dataset status
        sa.Column(
            "status",
            sa.Enum("AVAILABLE", "PREPARING", "ARCHIVED", "ERROR", name="datasetstatus"),
            nullable=False,
            server_default="PREPARING",
            comment="数据集状态: AVAILABLE=可用, PREPARING=准备中, ARCHIVED=已归档, ERROR=错误",
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
            "last_accessed_at",
            sa.DateTime(),
            nullable=True,
            comment="最后访问时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_datasets_owner_id",
            ondelete="CASCADE",
        ),
        comment="数据集表",
    )

    # Create unique constraint for (name, version)
    op.create_unique_constraint(
        "uk_datasets_name_version",
        "datasets",
        ["name", "version"],
    )

    # Create indexes
    op.create_index(
        "ix_datasets_owner_id",
        "datasets",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        "ix_datasets_storage_type",
        "datasets",
        ["storage_type"],
        unique=False,
    )
    op.create_index(
        "ix_datasets_dataset_type",
        "datasets",
        ["dataset_type"],
        unique=False,
    )
    op.create_index(
        "ix_datasets_status",
        "datasets",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_datasets_created_at",
        "datasets",
        ["created_at"],
        unique=False,
    )

    # Create fulltext index for name and description search
    op.execute("ALTER TABLE datasets ADD FULLTEXT INDEX ft_datasets_name_desc (name, description)")


def downgrade() -> None:
    # Drop table (MySQL automatically drops all indexes and constraints)
    op.drop_table("datasets")

    # Drop enum types
    sa.Enum(name="datasetstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="datasetvisibility").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="datasettype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="datasetstoragetype").drop(op.get_bind(), checkfirst=True)
