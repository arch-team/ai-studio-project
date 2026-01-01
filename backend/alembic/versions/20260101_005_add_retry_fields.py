"""Add retry_count and last_retry_at fields to training_jobs

Revision ID: 20260101_005
Revises: 20260101_004
Create Date: 2026-01-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260101_005'
down_revision: Union[str, None] = '20260101_004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add auto-recovery retry mechanism fields."""

    # 添加retry_count字段
    op.add_column(
        'training_jobs',
        sa.Column(
            'retry_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='重试次数'
        )
    )

    # 添加last_retry_at字段
    op.add_column(
        'training_jobs',
        sa.Column(
            'last_retry_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='最后重试时间'
        )
    )

    # 创建索引以优化查询失败且未超过重试次数的任务
    op.create_index(
        'ix_training_jobs_status_retry',
        'training_jobs',
        ['status', 'retry_count'],
        unique=False
    )


def downgrade() -> None:
    """Remove auto-recovery retry mechanism fields."""

    # 删除索引
    op.drop_index('ix_training_jobs_status_retry', table_name='training_jobs')

    # 删除字段
    op.drop_column('training_jobs', 'last_retry_at')
    op.drop_column('training_jobs', 'retry_count')
