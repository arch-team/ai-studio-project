"""add space backend fields

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-06-13 14:00:00.000000

为 development_spaces 表新增 HyperPod 后端支持字段:
- backend: SpaceBackend 枚举 (STUDIO/HYPERPOD)，默认 STUDIO，向后兼容存量数据
- namespace: HyperPod CRD namespace (HyperPod 后端专属)
- queue_name: Kueue local queue (HyperPod 后端专属)
- workspace_template: WorkspaceTemplate 引用 (HyperPod 后端专属)

按 .name 持久化枚举值 (STUDIO/HYPERPOD 大写)，与 spaces 模块现有枚举列
(instance_type/status) 保持一致。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. backend 列 - 枚举值按 .name 大写持久化 (STUDIO/HYPERPOD)
    op.add_column(
        "development_spaces",
        sa.Column(
            "backend",
            sa.Enum("STUDIO", "HYPERPOD", name="spacebackend"),
            nullable=False,
            server_default="STUDIO",  # 默认值 STUDIO (向后兼容)
            comment="开发环境后端类型",
        ),
    )
    op.create_index(
        op.f("ix_development_spaces_backend"),
        "development_spaces",
        ["backend"],
        unique=False,
    )

    # 2-4. HyperPod 后端专属字段 (nullable)
    op.add_column(
        "development_spaces",
        sa.Column(
            "namespace",
            sa.String(length=255),
            nullable=True,
            comment="HyperPod CRD namespace",
        ),
    )
    op.add_column(
        "development_spaces",
        sa.Column(
            "queue_name",
            sa.String(length=255),
            nullable=True,
            comment="Kueue local queue",
        ),
    )
    op.add_column(
        "development_spaces",
        sa.Column(
            "workspace_template",
            sa.String(length=255),
            nullable=True,
            comment="WorkspaceTemplate 引用",
        ),
    )


def downgrade() -> None:
    op.drop_column("development_spaces", "workspace_template")
    op.drop_column("development_spaces", "queue_name")
    op.drop_column("development_spaces", "namespace")
    op.drop_index(op.f("ix_development_spaces_backend"), table_name="development_spaces")
    op.drop_column("development_spaces", "backend")
