"""add auto_resume_checkpoint_id to training_jobs

Revision ID: 7e1f2g5h4i6j
Revises: 6d0e1f4a3b5c
Create Date: 2026-01-15 10:03:00.000000

Adds auto_resume_checkpoint_id column for HyperPod Elastic Agent auto-recovery.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7e1f2g5h4i6j"
down_revision: Union[str, None] = "6d0e1f4a3b5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add auto_resume_checkpoint_id column
    op.add_column(
        "training_jobs",
        sa.Column(
            "auto_resume_checkpoint_id",
            sa.BigInteger(),
            nullable=True,
            comment="自动恢复检查点ID (HyperPod Elastic Agent 恢复时使用)",
        ),
    )

    # Create index
    op.create_index(
        "ix_training_jobs_auto_resume_checkpoint_id",
        "training_jobs",
        ["auto_resume_checkpoint_id"],
        unique=False,
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_training_jobs_auto_resume_checkpoint_id",
        "training_jobs",
        "checkpoints",
        ["auto_resume_checkpoint_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint(
        "fk_training_jobs_auto_resume_checkpoint_id",
        "training_jobs",
        type_="foreignkey",
    )

    # Drop index
    op.drop_index(
        "ix_training_jobs_auto_resume_checkpoint_id",
        table_name="training_jobs",
    )

    # Drop column
    op.drop_column("training_jobs", "auto_resume_checkpoint_id")
