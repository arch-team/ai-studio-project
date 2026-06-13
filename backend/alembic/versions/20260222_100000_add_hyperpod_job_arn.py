"""add hyperpod_job_arn to training_jobs

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-22 10:00:00.000000

Adds hyperpod_job_arn column for storing HyperPod Job ARN.
This column was defined in the ORM model but missing from migrations.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "training_jobs",
        sa.Column(
            "hyperpod_job_arn",
            sa.String(length=512),
            nullable=True,
            comment="HyperPod训练任务ARN",
        ),
    )


def downgrade() -> None:
    op.drop_column("training_jobs", "hyperpod_job_arn")
