"""Add Kueue priority and queue fields to training_jobs

Revision ID: 20260101_004
Revises: 20251230_003
Create Date: 2026-01-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260101_004'
down_revision: Union[str, None] = '20251230_003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Kueue Gang Scheduling support fields."""

    # 添加priority字段
    op.add_column(
        'training_jobs',
        sa.Column(
            'priority',
            sa.String(50),
            nullable=True,
            comment='Kueue优先级类别: low, normal, high'
        )
    )

    # 添加queue_name字段
    op.add_column(
        'training_jobs',
        sa.Column(
            'queue_name',
            sa.String(100),
            nullable=True,
            comment='Kueue LocalQueue名称,默认使用项目队列'
        )
    )

    # 为已存在的训练任务设置默认priority='normal'
    op.execute("UPDATE training_jobs SET priority = 'normal' WHERE priority IS NULL")

    # 创建索引以优化按优先级查询
    op.create_index(
        'ix_training_jobs_priority',
        'training_jobs',
        ['priority'],
        unique=False
    )


def downgrade() -> None:
    """Remove Kueue Gang Scheduling support fields."""

    # 删除索引
    op.drop_index('ix_training_jobs_priority', table_name='training_jobs')

    # 删除字段
    op.drop_column('training_jobs', 'queue_name')
    op.drop_column('training_jobs', 'priority')
