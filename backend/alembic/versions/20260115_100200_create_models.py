"""create models table

Revision ID: 6d0e1f4a3b5c
Revises: 5c9d0e3f2a4b
Create Date: 2026-01-15 10:02:00.000000

Creates the models table for storing trained model metadata.
Supports model versioning and SageMaker Model Registry integration.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "6d0e1f4a3b5c"
down_revision: Union[str, None] = "5c9d0e3f2a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create models table
    op.create_table(
        "models",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="模型ID",
        ),
        # Model identification
        sa.Column(
            "model_name",
            sa.String(length=128),
            nullable=False,
            comment="模型名称",
        ),
        sa.Column(
            "version",
            sa.String(length=32),
            nullable=False,
            server_default="v1",
            comment="模型版本",
        ),
        sa.Column(
            "display_name",
            sa.String(length=256),
            nullable=True,
            comment="显示名称",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="模型描述",
        ),
        # Associated training job and checkpoint
        sa.Column(
            "training_job_id",
            sa.BigInteger(),
            nullable=True,
            comment="关联训练任务ID",
        ),
        sa.Column(
            "checkpoint_id",
            sa.BigInteger(),
            nullable=True,
            comment="关联检查点ID",
        ),
        # Owner
        sa.Column(
            "owner_id",
            sa.BigInteger(),
            nullable=False,
            comment="所有者用户ID",
        ),
        # Storage location
        sa.Column(
            "model_uri",
            sa.String(length=512),
            nullable=True,
            comment="模型存储路径 (S3 URI)",
        ),
        # SageMaker Model Registry integration
        sa.Column(
            "registry_arn",
            sa.String(length=512),
            nullable=True,
            comment="SageMaker Model Registry ARN",
        ),
        sa.Column(
            "registry_status",
            sa.String(length=32),
            nullable=True,
            comment="Registry 同步状态",
        ),
        # Model metrics (training results)
        sa.Column(
            "metrics",
            mysql.JSON(),
            nullable=True,
            comment="模型指标 (JSON: accuracy, loss, f1_score 等)",
        ),
        # Hyperparameters used for training
        sa.Column(
            "hyperparameters",
            mysql.JSON(),
            nullable=True,
            comment="训练超参数 (JSON)",
        ),
        # Model framework
        sa.Column(
            "framework",
            sa.Enum("PYTORCH", "TENSORFLOW", "JAX", "OTHER", name="modelframework"),
            nullable=False,
            server_default="PYTORCH",
            comment="模型框架",
        ),
        sa.Column(
            "framework_version",
            sa.String(length=32),
            nullable=True,
            comment="框架版本 (例如: 2.1.0)",
        ),
        # Model status
        sa.Column(
            "status",
            sa.Enum(
                "TRAINING",
                "REGISTERED",
                "DEPLOYED",
                "ARCHIVED",
                "FAILED",
                name="modelstatus",
            ),
            nullable=False,
            server_default="TRAINING",
            comment="模型状态",
        ),
        # Model size and format
        sa.Column(
            "size_bytes",
            sa.BigInteger(),
            nullable=True,
            comment="模型大小 (字节)",
        ),
        sa.Column(
            "model_format",
            sa.String(length=64),
            nullable=True,
            comment="模型格式 (例如: safetensors, pickle, onnx)",
        ),
        # Tags for organization
        sa.Column(
            "tags",
            mysql.JSON(),
            nullable=True,
            comment="标签 (JSON 数组)",
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
            "registered_at",
            sa.DateTime(),
            nullable=True,
            comment="注册到 Registry 的时间",
        ),
        sa.Column(
            "archived_at",
            sa.DateTime(),
            nullable=True,
            comment="归档时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        # Unique constraint: model_name + version combination must be unique
        sa.UniqueConstraint(
            "model_name",
            "version",
            name="uk_models_name_version",
        ),
        sa.ForeignKeyConstraint(
            ["training_job_id"],
            ["training_jobs.id"],
            name="fk_models_training_job_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["checkpoint_id"],
            ["checkpoints.id"],
            name="fk_models_checkpoint_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_models_owner_id",
            ondelete="CASCADE",
        ),
        comment="模型表",
    )

    # Create indexes
    op.create_index(
        "ix_models_model_name",
        "models",
        ["model_name"],
        unique=False,
    )
    op.create_index(
        "ix_models_training_job_id",
        "models",
        ["training_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_models_checkpoint_id",
        "models",
        ["checkpoint_id"],
        unique=False,
    )
    op.create_index(
        "ix_models_owner_id",
        "models",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        "ix_models_framework",
        "models",
        ["framework"],
        unique=False,
    )
    op.create_index(
        "ix_models_status",
        "models",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_models_created_at",
        "models",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_models_registry_arn",
        "models",
        ["registry_arn"],
        unique=False,
    )
    # Composite index for owner + status queries
    op.create_index(
        "ix_models_owner_status",
        "models",
        ["owner_id", "status"],
        unique=False,
    )
    # Composite index for training_job + status queries
    op.create_index(
        "ix_models_job_status",
        "models",
        ["training_job_id", "status"],
        unique=False,
    )

    # Create fulltext index for model_name and description search
    op.execute(
        "ALTER TABLE models ADD FULLTEXT INDEX ft_models_search (model_name, description)"
    )


def downgrade() -> None:
    # Drop fulltext index
    op.execute("ALTER TABLE models DROP INDEX ft_models_search")

    # Drop indexes
    op.drop_index("ix_models_job_status", table_name="models")
    op.drop_index("ix_models_owner_status", table_name="models")
    op.drop_index("ix_models_registry_arn", table_name="models")
    op.drop_index("ix_models_created_at", table_name="models")
    op.drop_index("ix_models_status", table_name="models")
    op.drop_index("ix_models_framework", table_name="models")
    op.drop_index("ix_models_owner_id", table_name="models")
    op.drop_index("ix_models_checkpoint_id", table_name="models")
    op.drop_index("ix_models_training_job_id", table_name="models")
    op.drop_index("ix_models_model_name", table_name="models")

    # Drop table
    op.drop_table("models")

    # Drop enum types
    sa.Enum(name="modelstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="modelframework").drop(op.get_bind(), checkfirst=True)
