"""add checkpoints.trigger_type column

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-06-12 10:00:00.000000

CheckpointModel 已定义 trigger_type 列（5 种检查点触发场景），
但建表迁移 20260115_100100 未包含，导致 ORM 查询 1054 Unknown column。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "checkpoints",
        sa.Column(
            "trigger_type",
            sa.Enum("SCHEDULED", "INTERRUPT", "NODE_FAILURE", "PREEMPTION", "MANUAL", name="checkpointtriggertype"),
            nullable=False,
            server_default="SCHEDULED",
            comment="触发类型",
        ),
    )


def downgrade() -> None:
    op.drop_column("checkpoints", "trigger_type")
