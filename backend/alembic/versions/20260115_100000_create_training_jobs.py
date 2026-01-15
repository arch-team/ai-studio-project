"""create training_jobs table

Revision ID: 4b8c9d2e1f3a
Revises: a743f443fb73
Create Date: 2026-01-15 10:00:00.000000

Creates the training_jobs table for storing training task metadata,
corresponding to HyperPod SDK's HyperPodPytorchJob resources.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "4b8c9d2e1f3a"
down_revision: Union[str, None] = "a743f443fb73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create training_jobs table
    op.create_table(
        "training_jobs",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="训练任务ID",
        ),
        # Job identification
        sa.Column(
            "job_name",
            sa.String(length=128),
            nullable=False,
            comment="任务名称 (HyperPod Job 名称)",
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
            comment="任务描述",
        ),
        # Owner
        sa.Column(
            "owner_id",
            sa.BigInteger(),
            nullable=False,
            comment="所有者用户ID",
        ),
        # Training configuration
        sa.Column(
            "image_uri",
            sa.String(length=512),
            nullable=False,
            comment="Docker 镜像 URI",
        ),
        sa.Column(
            "instance_type",
            sa.String(length=64),
            nullable=False,
            comment="实例类型 (例如: ml.p4d.24xlarge)",
        ),
        sa.Column(
            "node_count",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="节点数量",
        ),
        sa.Column(
            "tasks_per_node",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="每节点任务数 (GPU 数量)",
        ),
        # Entrypoint and environment
        sa.Column(
            "entrypoint_command",
            mysql.JSON(),
            nullable=False,
            comment="启动命令 (JSON 数组)",
        ),
        sa.Column(
            "environment_variables",
            mysql.JSON(),
            nullable=True,
            comment="环境变量 (JSON 对象)",
        ),
        # Dataset configuration (FK to datasets deferred to Phase 4)
        sa.Column(
            "dataset_id",
            sa.BigInteger(),
            nullable=True,
            comment="关联数据集ID (FK 在 Phase 4 添加)",
        ),
        sa.Column(
            "data_mount_path",
            sa.String(length=256),
            nullable=True,
            comment="数据挂载路径 (例如: /data)",
        ),
        # Checkpoint configuration
        sa.Column(
            "checkpoint_mount_path",
            sa.String(length=256),
            nullable=True,
            comment="检查点挂载路径 (例如: /checkpoints)",
        ),
        sa.Column(
            "checkpoint_interval",
            sa.Integer(),
            nullable=True,
            comment="检查点保存间隔 (epoch)",
        ),
        # Training parameters
        sa.Column(
            "hyperparameters",
            mysql.JSON(),
            nullable=True,
            comment="超参数 (JSON 对象)",
        ),
        sa.Column(
            "max_epochs",
            sa.Integer(),
            nullable=True,
            comment="最大训练轮数",
        ),
        sa.Column(
            "batch_size",
            sa.Integer(),
            nullable=True,
            comment="批次大小",
        ),
        sa.Column(
            "learning_rate",
            sa.DECIMAL(precision=10, scale=8),
            nullable=True,
            comment="学习率",
        ),
        # Distribution strategy
        sa.Column(
            "distribution_strategy",
            sa.Enum("DDP", "FSDP", "DEEPSPEED", "HOROVOD", name="distributionstrategy"),
            nullable=False,
            server_default="DDP",
            comment="分布式策略",
        ),
        sa.Column(
            "mixed_precision",
            sa.Boolean(),
            nullable=False,
            server_default="0",
            comment="是否使用混合精度训练 (AMP)",
        ),
        # Spot instance configuration
        sa.Column(
            "use_spot_instances",
            sa.Boolean(),
            nullable=False,
            server_default="0",
            comment="是否使用 Spot 实例",
        ),
        sa.Column(
            "spot_interruption_behavior",
            sa.Enum("STOP", "TERMINATE", "HIBERNATE", name="spotinterruptionbehavior"),
            nullable=True,
            server_default="STOP",
            comment="Spot 中断行为",
        ),
        # Priority (FR-004 preemptive scheduling)
        sa.Column(
            "priority",
            sa.Enum("HIGH", "MEDIUM", "LOW", name="jobpriority"),
            nullable=False,
            server_default="MEDIUM",
            comment="任务优先级 (用于抢占式调度)",
        ),
        # Job status (spec.md state machine)
        sa.Column(
            "status",
            sa.Enum(
                "SUBMITTED",
                "RUNNING",
                "PAUSED",
                "PREEMPTED",
                "COMPLETED",
                "FAILED",
                name="jobstatus",
            ),
            nullable=False,
            server_default="SUBMITTED",
            comment="任务状态",
        ),
        # HyperPod/Kueue status mapping
        sa.Column(
            "hyperpod_status",
            sa.String(length=64),
            nullable=True,
            comment="HyperPod Job 原始状态",
        ),
        sa.Column(
            "kueue_workload_name",
            sa.String(length=128),
            nullable=True,
            comment="Kueue Workload 名称",
        ),
        sa.Column(
            "kueue_status",
            sa.String(length=64),
            nullable=True,
            comment="Kueue Workload 状态",
        ),
        # Pod statistics
        sa.Column(
            "total_pods",
            sa.Integer(),
            nullable=True,
            comment="总 Pod 数量",
        ),
        sa.Column(
            "running_pods",
            sa.Integer(),
            nullable=True,
            server_default="0",
            comment="运行中 Pod 数量",
        ),
        sa.Column(
            "failed_pods",
            sa.Integer(),
            nullable=True,
            server_default="0",
            comment="失败 Pod 数量",
        ),
        # Preemption statistics (for consecutive preemption failure detection)
        sa.Column(
            "preemption_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="累计被抢占次数",
        ),
        # Training metrics (latest values)
        sa.Column(
            "current_epoch",
            sa.Integer(),
            nullable=True,
            comment="当前训练轮次",
        ),
        sa.Column(
            "current_step",
            sa.BigInteger(),
            nullable=True,
            comment="当前训练步数",
        ),
        sa.Column(
            "latest_loss",
            sa.DECIMAL(precision=10, scale=6),
            nullable=True,
            comment="最新损失值",
        ),
        sa.Column(
            "latest_accuracy",
            sa.DECIMAL(precision=5, scale=4),
            nullable=True,
            comment="最新准确率",
        ),
        # Time statistics
        sa.Column(
            "submitted_at",
            sa.DateTime(),
            nullable=True,
            comment="提交时间",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=True,
            comment="开始时间",
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            nullable=True,
            comment="完成时间",
        ),
        sa.Column(
            "duration_seconds",
            sa.Integer(),
            nullable=True,
            comment="运行时长 (秒)",
        ),
        # Resource statistics
        sa.Column(
            "total_gpu_hours",
            sa.DECIMAL(precision=12, scale=2),
            nullable=True,
            comment="总 GPU 时",
        ),
        sa.Column(
            "estimated_cost_usd",
            sa.DECIMAL(precision=12, scale=2),
            nullable=True,
            comment="预估成本 (USD)",
        ),
        # Error information
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="错误信息",
        ),
        sa.Column(
            "failure_reason",
            sa.String(length=512),
            nullable=True,
            comment="失败原因",
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_name"),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_training_jobs_owner_id",
            ondelete="CASCADE",
        ),
        comment="训练任务表",
    )

    # Create indexes
    op.create_index(
        "ix_training_jobs_job_name",
        "training_jobs",
        ["job_name"],
        unique=True,
    )
    op.create_index(
        "ix_training_jobs_owner_id",
        "training_jobs",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        "ix_training_jobs_status",
        "training_jobs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_training_jobs_priority",
        "training_jobs",
        ["priority"],
        unique=False,
    )
    op.create_index(
        "ix_training_jobs_dataset_id",
        "training_jobs",
        ["dataset_id"],
        unique=False,
    )
    op.create_index(
        "ix_training_jobs_submitted_at",
        "training_jobs",
        ["submitted_at"],
        unique=False,
    )
    op.create_index(
        "ix_training_jobs_completed_at",
        "training_jobs",
        ["completed_at"],
        unique=False,
    )
    op.create_index(
        "ix_training_jobs_hyperpod_status",
        "training_jobs",
        ["hyperpod_status"],
        unique=False,
    )
    op.create_index(
        "ix_training_jobs_kueue_workload_name",
        "training_jobs",
        ["kueue_workload_name"],
        unique=False,
    )
    # Composite index for status + priority queries
    op.create_index(
        "ix_training_jobs_status_priority",
        "training_jobs",
        ["status", "priority"],
        unique=False,
    )
    # Composite index for owner + status + created_at queries
    op.create_index(
        "ix_training_jobs_owner_status_created",
        "training_jobs",
        ["owner_id", "status", "created_at"],
        unique=False,
    )

    # Create fulltext index for job_name and description search
    op.execute(
        "ALTER TABLE training_jobs ADD FULLTEXT INDEX ft_training_jobs_search (job_name, description)"
    )

    # Create BEFORE UPDATE trigger to validate state transitions
    op.execute(
        """
        CREATE TRIGGER validate_training_job_state_transition_trigger
        BEFORE UPDATE ON training_jobs
        FOR EACH ROW
        BEGIN
            -- Only validate if status is changing
            IF OLD.status != NEW.status THEN
                IF NOT validate_training_job_state_transition(OLD.status, NEW.status) THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Invalid training job state transition';
                END IF;
            END IF;
        END;
        """
    )


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS validate_training_job_state_transition_trigger")

    # Drop fulltext index
    op.execute("ALTER TABLE training_jobs DROP INDEX ft_training_jobs_search")

    # Drop indexes
    op.drop_index("ix_training_jobs_owner_status_created", table_name="training_jobs")
    op.drop_index("ix_training_jobs_status_priority", table_name="training_jobs")
    op.drop_index("ix_training_jobs_kueue_workload_name", table_name="training_jobs")
    op.drop_index("ix_training_jobs_hyperpod_status", table_name="training_jobs")
    op.drop_index("ix_training_jobs_completed_at", table_name="training_jobs")
    op.drop_index("ix_training_jobs_submitted_at", table_name="training_jobs")
    op.drop_index("ix_training_jobs_dataset_id", table_name="training_jobs")
    op.drop_index("ix_training_jobs_priority", table_name="training_jobs")
    op.drop_index("ix_training_jobs_status", table_name="training_jobs")
    op.drop_index("ix_training_jobs_owner_id", table_name="training_jobs")
    op.drop_index("ix_training_jobs_job_name", table_name="training_jobs")

    # Drop table
    op.drop_table("training_jobs")

    # Drop enum types
    sa.Enum(name="jobstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="jobpriority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="spotinterruptionbehavior").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="distributionstrategy").drop(op.get_bind(), checkfirst=True)
