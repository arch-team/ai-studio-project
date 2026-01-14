"""create training_job_state_transition_constraints

Revision ID: 7778e77de8a6
Revises: 206d5baf77c1
Create Date: 2026-01-14 22:12:09.589569

This migration creates the training job state transition rules table
and seeds the valid state transitions based on the spec.md state model:

State Transitions:
- Submitted → Running, Failed
- Running → Paused, Preempted, Completed, Failed
- Paused → Running, Failed
- Preempted → Running, Failed
- Completed → (terminal state)
- Failed → (terminal state)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7778e77de8a6"
down_revision: Union[str, None] = "206d5baf77c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valid state transitions based on spec.md Training Job State Model
STATE_TRANSITIONS = [
    # From SUBMITTED
    ("SUBMITTED", "RUNNING", "Job started execution"),
    ("SUBMITTED", "FAILED", "Job failed during submission/initialization"),
    # From RUNNING
    ("RUNNING", "PAUSED", "Job paused by user or system"),
    ("RUNNING", "PREEMPTED", "Job preempted due to resource constraints"),
    ("RUNNING", "COMPLETED", "Job finished successfully"),
    ("RUNNING", "FAILED", "Job failed during execution"),
    # From PAUSED
    ("PAUSED", "RUNNING", "Job resumed from pause"),
    ("PAUSED", "FAILED", "Job failed while paused"),
    # From PREEMPTED
    ("PREEMPTED", "RUNNING", "Job resumed after preemption"),
    ("PREEMPTED", "FAILED", "Job failed after preemption"),
    # COMPLETED and FAILED are terminal states (no outgoing transitions)
]


def upgrade() -> None:
    # Create training_job_state_transitions table
    op.create_table(
        "training_job_state_transitions",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="转换规则ID",
        ),
        sa.Column(
            "from_status",
            sa.String(length=32),
            nullable=False,
            comment="源状态",
        ),
        sa.Column(
            "to_status",
            sa.String(length=32),
            nullable=False,
            comment="目标状态",
        ),
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=True,
            comment="转换描述",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
            comment="是否启用",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="创建时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("from_status", "to_status", name="uq_state_transition"),
        comment="训练任务状态转换规则表",
    )

    # Create indexes
    op.create_index(
        "ix_training_job_state_transitions_from_status",
        "training_job_state_transitions",
        ["from_status"],
        unique=False,
    )
    op.create_index(
        "ix_training_job_state_transitions_lookup",
        "training_job_state_transitions",
        ["from_status", "to_status", "is_active"],
        unique=False,
    )

    # Seed valid state transitions
    transitions_table = sa.table(
        "training_job_state_transitions",
        sa.column("from_status", sa.String),
        sa.column("to_status", sa.String),
        sa.column("description", sa.String),
        sa.column("is_active", sa.Boolean),
    )

    op.bulk_insert(
        transitions_table,
        [
            {
                "from_status": from_s,
                "to_status": to_s,
                "description": desc,
                "is_active": True,
            }
            for from_s, to_s, desc in STATE_TRANSITIONS
        ],
    )

    # Create stored function to validate state transitions
    # This function will be used by a trigger when training_jobs table is created
    op.execute(
        """
        CREATE FUNCTION validate_training_job_state_transition(
            old_status VARCHAR(32),
            new_status VARCHAR(32)
        ) RETURNS BOOLEAN
        DETERMINISTIC
        READS SQL DATA
        BEGIN
            DECLARE is_valid INT DEFAULT 0;

            -- Same status is always allowed (no actual transition)
            IF old_status = new_status THEN
                RETURN TRUE;
            END IF;

            -- Check if transition exists and is active
            SELECT COUNT(*) INTO is_valid
            FROM training_job_state_transitions
            WHERE from_status = old_status
              AND to_status = new_status
              AND is_active = TRUE;

            RETURN is_valid > 0;
        END;
        """
    )


def downgrade() -> None:
    # Drop the stored function
    op.execute("DROP FUNCTION IF EXISTS validate_training_job_state_transition")

    # Drop indexes
    op.drop_index(
        "ix_training_job_state_transitions_lookup",
        table_name="training_job_state_transitions",
    )
    op.drop_index(
        "ix_training_job_state_transitions_from_status",
        table_name="training_job_state_transitions",
    )

    # Drop table
    op.drop_table("training_job_state_transitions")
