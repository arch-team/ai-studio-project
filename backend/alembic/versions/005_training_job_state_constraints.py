"""Create training_job_state_transitions table.

Revision ID: 005_training_job_state_constraints
Revises: 004_create_development_spaces
Create Date: 2026-01-12

Task: T010d - 创建训练任务状态转换约束
实现数据库级状态转换验证,防止非法状态转换 (如 Completed → Running):
- 状态转换矩阵表: 创建 training_job_state_transitions 表存储合法状态转换规则
- CHECK 约束: 在 training_jobs 表添加 CHECK 约束验证状态枚举值有效性
- 更新触发器: 将在 Phase 3 T021 之后创建 (需要 training_jobs 表存在)

注意: 触发器部分将在 Phase 3 T021 (training_jobs 表) 创建后通过单独迁移添加
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "005_training_job_state_constraints"
down_revision: Union[str, None] = "004_create_development_spaces"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 训练任务状态枚举 (与 spec.md Training Job State Model 一致)
TRAINING_JOB_STATUS = sa.Enum(
    "submitted",
    "running",
    "paused",
    "preempted",
    "completed",
    "failed",
    name="training_job_status",
)


def upgrade() -> None:
    """Create training_job_state_transitions table and initialize transition rules."""
    # 创建状态转换矩阵表
    op.create_table(
        "training_job_state_transitions",
        sa.Column(
            "id",
            mysql.INTEGER(unsigned=True),
            autoincrement=True,
            nullable=False,
            comment="转换规则ID",
        ),
        # 状态转换定义
        sa.Column(
            "from_status",
            TRAINING_JOB_STATUS,
            nullable=False,
            comment="源状态",
        ),
        sa.Column(
            "to_status",
            TRAINING_JOB_STATUS,
            nullable=False,
            comment="目标状态",
        ),
        # 转换控制
        sa.Column(
            "is_allowed",
            sa.Boolean(),
            nullable=False,
            server_default="1",
            comment="是否允许此转换",
        ),
        sa.Column(
            "is_terminal",
            sa.Boolean(),
            nullable=False,
            server_default="0",
            comment="目标状态是否为终态",
        ),
        # 转换描述
        sa.Column(
            "description",
            sa.String(256),
            nullable=True,
            comment="转换描述",
        ),
        sa.Column(
            "trigger_condition",
            sa.String(512),
            nullable=True,
            comment="触发条件描述",
        ),
        # 审计字段
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=3),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(3)"),
            comment="创建时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("from_status", "to_status", name="uk_state_transitions_from_to"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="训练任务状态转换矩阵表",
    )

    # 创建索引
    op.create_index(
        "idx_state_transitions_from_status",
        "training_job_state_transitions",
        ["from_status"],
    )
    op.create_index(
        "idx_state_transitions_to_status",
        "training_job_state_transitions",
        ["to_status"],
    )
    op.create_index(
        "idx_state_transitions_is_allowed",
        "training_job_state_transitions",
        ["is_allowed"],
    )

    # 初始化状态转换规则数据 (基于 spec.md Training Job State Model L533-547)
    op.execute("""
        INSERT INTO training_job_state_transitions
            (from_status, to_status, is_allowed, is_terminal, description, trigger_condition)
        VALUES
        -- 从 Submitted 状态的转换
        ('submitted', 'running', TRUE, FALSE, 'Submitted → Running', 'Kueue: Admitted=True AND PodsReady=True'),
        ('submitted', 'failed', TRUE, TRUE, 'Submitted → Failed', '配置验证失败 OR Gang Scheduling 连续失败 OR 权限拒绝'),

        -- 从 Running 状态的转换
        ('running', 'paused', TRUE, FALSE, 'Running → Paused', '用户调用 POST /training-jobs/{id}/actions/pause'),
        ('running', 'preempted', TRUE, FALSE, 'Running → Preempted', 'Kueue: Evicted=True (reason: Preempted)'),
        ('running', 'completed', TRUE, TRUE, 'Running → Completed', '训练脚本 exit code=0 AND Kueue: Finished=True'),
        ('running', 'failed', TRUE, TRUE, 'Running → Failed', '脚本 exit code!=0 OR 节点故障无可用检查点 OR 连续恢复失败>3次'),

        -- 从 Paused 状态的转换
        ('paused', 'running', TRUE, FALSE, 'Paused → Running', '用户调用 POST /training-jobs/{id}/actions/resume'),
        ('paused', 'failed', TRUE, TRUE, 'Paused → Failed', '用户调用 DELETE /training-jobs/{id}'),

        -- 从 Preempted 状态的转换
        ('preempted', 'submitted', TRUE, FALSE, 'Preempted → Submitted', '系统自动重新提交 (立即执行)'),
        ('preempted', 'running', TRUE, FALSE, 'Preempted → Running', 'Kueue 快速重新接纳 (资源立即可用场景)'),
        ('preempted', 'failed', TRUE, TRUE, 'Preempted → Failed', '连续抢占恢复失败>3次'),

        -- 终态禁止转换规则 (Completed)
        ('completed', 'submitted', FALSE, FALSE, 'Completed → Submitted (禁止)', '终态不可转换'),
        ('completed', 'running', FALSE, FALSE, 'Completed → Running (禁止)', '终态不可转换'),
        ('completed', 'paused', FALSE, FALSE, 'Completed → Paused (禁止)', '终态不可转换'),
        ('completed', 'preempted', FALSE, FALSE, 'Completed → Preempted (禁止)', '终态不可转换'),
        ('completed', 'failed', FALSE, FALSE, 'Completed → Failed (禁止)', '终态不可转换'),

        -- 终态禁止转换规则 (Failed)
        ('failed', 'submitted', FALSE, FALSE, 'Failed → Submitted (禁止)', '终态不可转换'),
        ('failed', 'running', FALSE, FALSE, 'Failed → Running (禁止)', '终态不可转换'),
        ('failed', 'paused', FALSE, FALSE, 'Failed → Paused (禁止)', '终态不可转换'),
        ('failed', 'preempted', FALSE, FALSE, 'Failed → Preempted (禁止)', '终态不可转换'),
        ('failed', 'completed', FALSE, FALSE, 'Failed → Completed (禁止)', '终态不可转换')
    """)


def downgrade() -> None:
    """Drop training_job_state_transitions table."""
    op.drop_index("idx_state_transitions_is_allowed", table_name="training_job_state_transitions")
    op.drop_index("idx_state_transitions_to_status", table_name="training_job_state_transitions")
    op.drop_index("idx_state_transitions_from_status", table_name="training_job_state_transitions")
    op.drop_table("training_job_state_transitions")
