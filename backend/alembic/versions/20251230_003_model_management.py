"""模型管理表迁移

Revision ID: 003
Revises: 002
Create Date: 2025-12-30

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建models表
    # 注意: 枚举类型会由SQLAlchemy自动创建
    op.create_table(
        "models",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("framework", sa.Enum("PYTORCH", "TENSORFLOW", "ONNX", "JFLUX", "HUGGINGFACE", "CUSTOM", name="modelframework"), nullable=False, index=True),
        sa.Column("task_type", sa.String(50), nullable=True, index=True),
        sa.Column("project_id", sa.Integer(), nullable=False, index=True),
        sa.Column("creator_id", sa.Integer(), nullable=False, index=True),
        sa.Column("source_training_job_id", sa.Integer(), nullable=True, index=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("latest_version", sa.String(50), nullable=True),
        sa.Column("latest_version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_training_job_id"], ["training_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建model_versions表
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False, index=True),
        sa.Column("version", sa.String(50), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("UPLOADING", "PROCESSING", "AVAILABLE", "FAILED", "ARCHIVED", name="modelstatus"), nullable=False, index=True, server_default="PROCESSING"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("storage_size_bytes", sa.Integer(), nullable=True),
        sa.Column("checksum_md5", sa.String(32), nullable=True),
        sa.Column("model_format", sa.String(50), nullable=True),
        sa.Column("model_architecture", sa.String(100), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("hyperparameters", sa.JSON(), nullable=True),
        sa.Column("dependencies", sa.JSON(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("published_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["published_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建model_deployments表
    op.create_table(
        "model_deployments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_version_id", sa.Integer(), nullable=False, index=True),
        sa.Column("deployed_by_id", sa.Integer(), nullable=False),
        sa.Column("deployment_name", sa.String(100), nullable=False, index=True),
        sa.Column("deployment_type", sa.String(50), nullable=False),
        sa.Column("endpoint_url", sa.String(500), nullable=True),
        sa.Column("k8s_namespace", sa.String(63), nullable=True),
        sa.Column("k8s_deployment_name", sa.String(253), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING", index=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("stopped_at", sa.DateTime(), nullable=True),
        sa.Column("deployment_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deployed_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 索引已通过 index=True 参数自动创建


def downgrade() -> None:
    # 删除表
    op.drop_table("model_deployments")
    op.drop_table("model_versions")
    op.drop_table("models")

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS modelframework")
    op.execute("DROP TYPE IF EXISTS modelstatus")
