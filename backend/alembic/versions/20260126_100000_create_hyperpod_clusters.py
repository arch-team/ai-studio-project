"""create hyperpod_clusters table

Revision ID: a1b2c3d4e5f6
Revises: 9a1b2c3d4e5f
Create Date: 2026-01-26 10:00:00.000000

Creates the hyperpod_clusters table for caching HyperPod cluster metadata.
This table is a local cache; the source of truth is the HyperPod/K8s API.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "9a1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create hyperpod_clusters table
    op.create_table(
        "hyperpod_clusters",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="集群ID",
        ),
        # Cluster identification
        sa.Column(
            "cluster_name",
            sa.String(length=128),
            nullable=False,
            comment="集群名称",
        ),
        sa.Column(
            "cluster_arn",
            sa.String(length=512),
            nullable=False,
            comment="集群 ARN",
        ),
        sa.Column(
            "region",
            sa.String(length=32),
            nullable=False,
            comment="AWS 区域",
        ),
        sa.Column(
            "vpc_id",
            sa.String(length=64),
            nullable=False,
            comment="VPC ID",
        ),
        # Instance configuration
        sa.Column(
            "instance_groups",
            mysql.JSON(),
            nullable=False,
            comment="实例组配置 JSON",
        ),
        # Resource capacity
        sa.Column(
            "total_nodes",
            sa.Integer().with_variant(sa.Integer(), "mysql"),
            nullable=False,
            comment="总节点数",
        ),
        sa.Column(
            "available_nodes",
            sa.Integer().with_variant(sa.Integer(), "mysql"),
            nullable=False,
            server_default="0",
            comment="可用节点数",
        ),
        sa.Column(
            "total_cpu_cores",
            sa.Integer().with_variant(sa.Integer(), "mysql"),
            nullable=True,
            comment="总 CPU 核心数",
        ),
        sa.Column(
            "total_gpu_count",
            sa.Integer().with_variant(sa.Integer(), "mysql"),
            nullable=True,
            comment="总 GPU 数量",
        ),
        sa.Column(
            "total_memory_gb",
            sa.Integer().with_variant(sa.Integer(), "mysql"),
            nullable=True,
            comment="总内存 (GB)",
        ),
        # Status fields
        sa.Column(
            "status",
            sa.Enum(
                "creating",
                "active",
                "updating",
                "deleting",
                "failed",
                name="clusterstatus",
            ),
            nullable=False,
            server_default="creating",
            comment="集群状态",
        ),
        sa.Column(
            "health_status",
            sa.Enum(
                "healthy",
                "degraded",
                "unhealthy",
                name="healthstatus",
            ),
            nullable=True,
            comment="健康状态",
        ),
        # FSx integration
        sa.Column(
            "fsx_filesystem_id",
            sa.String(length=128),
            nullable=True,
            comment="FSx 文件系统 ID",
        ),
        sa.Column(
            "fsx_mount_point",
            sa.String(length=256),
            nullable=True,
            comment="FSx 挂载点",
        ),
        # Monitoring integration
        sa.Column(
            "prometheus_endpoint",
            sa.String(length=512),
            nullable=True,
            comment="Prometheus 端点",
        ),
        sa.Column(
            "grafana_workspace_id",
            sa.String(length=128),
            nullable=True,
            comment="Grafana 工作区 ID",
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
            "last_sync_at",
            sa.DateTime(),
            nullable=True,
            comment="最后同步时间",
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint("id", name="pk_hyperpod_clusters"),
    )

    # Create unique constraints
    op.create_unique_constraint(
        "uq_hyperpod_clusters_cluster_name",
        "hyperpod_clusters",
        ["cluster_name"],
    )
    op.create_unique_constraint(
        "uq_hyperpod_clusters_cluster_arn",
        "hyperpod_clusters",
        ["cluster_arn"],
    )

    # Create indexes
    op.create_index(
        "ix_hyperpod_clusters_region",
        "hyperpod_clusters",
        ["region"],
    )
    op.create_index(
        "ix_hyperpod_clusters_status",
        "hyperpod_clusters",
        ["status"],
    )
    op.create_index(
        "ix_hyperpod_clusters_health_status",
        "hyperpod_clusters",
        ["health_status"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_hyperpod_clusters_health_status", table_name="hyperpod_clusters")
    op.drop_index("ix_hyperpod_clusters_status", table_name="hyperpod_clusters")
    op.drop_index("ix_hyperpod_clusters_region", table_name="hyperpod_clusters")

    # Drop unique constraints
    op.drop_constraint(
        "uq_hyperpod_clusters_cluster_arn",
        "hyperpod_clusters",
        type_="unique",
    )
    op.drop_constraint(
        "uq_hyperpod_clusters_cluster_name",
        "hyperpod_clusters",
        type_="unique",
    )

    # Drop table
    op.drop_table("hyperpod_clusters")

    # Drop enums
    sa.Enum(name="healthstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="clusterstatus").drop(op.get_bind(), checkfirst=True)
