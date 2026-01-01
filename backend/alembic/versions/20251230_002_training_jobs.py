"""Add training jobs tables

Revision ID: 002
Revises: 001
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建训练任务相关表"""
    # 注意: 枚举类型会由SQLAlchemy自动创建

    # 创建training_jobs表
    op.create_table(
        'training_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='任务名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='任务描述'),
        sa.Column('status', postgresql.ENUM('PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', name='trainingjobstatus'), nullable=False, comment='任务状态'),
        sa.Column('job_type', postgresql.ENUM('SINGLE_NODE', 'DISTRIBUTED_DATA_PARALLEL', 'DISTRIBUTED_MODEL_PARALLEL', 'HYBRID_PARALLEL', name='trainingjobtype'), nullable=False, comment='任务类型'),
        sa.Column('framework', postgresql.ENUM('PYTORCH', 'TENSORFLOW', 'JFLUX', 'DEEPSPEED', 'MEGATRON', name='frameworktype'), nullable=False, comment='训练框架'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('creator_id', sa.Integer(), nullable=False, comment='创建者ID'),
        sa.Column('k8s_namespace', sa.String(length=63), nullable=False, comment='K8S命名空间'),
        sa.Column('k8s_job_name', sa.String(length=253), nullable=True, comment='K8S Job名称'),
        sa.Column('k8s_pod_names', sa.JSON(), nullable=True, comment='K8S Pod名称列表'),
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=True, comment='排队时间'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成时间'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('exit_code', sa.Integer(), nullable=True, comment='退出码'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='删除时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_training_jobs_id'), 'training_jobs', ['id'], unique=False)

    # 创建training_job_configs表
    op.create_table(
        'training_job_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False, comment='训练任务ID'),
        sa.Column('node_count', sa.Integer(), nullable=False, comment='节点数量'),
        sa.Column('gpu_per_node', sa.Integer(), nullable=False, comment='每节点GPU数'),
        sa.Column('cpu_per_node', sa.Integer(), nullable=False, comment='每节点CPU数'),
        sa.Column('memory_per_node_gb', sa.Integer(), nullable=False, comment='每节点内存(GB)'),
        sa.Column('gpu_type', sa.String(length=50), nullable=True, comment='GPU型号'),
        sa.Column('docker_image', sa.String(length=500), nullable=False, comment='Docker镜像'),
        sa.Column('command', sa.JSON(), nullable=False, comment='执行命令'),
        sa.Column('args', sa.JSON(), nullable=True, comment='命令参数'),
        sa.Column('env_vars', sa.JSON(), nullable=True, comment='环境变量'),
        sa.Column('dataset_path', sa.String(length=500), nullable=True, comment='数据集路径'),
        sa.Column('checkpoint_path', sa.String(length=500), nullable=True, comment='检查点路径'),
        sa.Column('output_path', sa.String(length=500), nullable=False, comment='输出路径'),
        sa.Column('hyperparameters', sa.JSON(), nullable=True, comment='超参数'),
        sa.Column('distributed_config', sa.JSON(), nullable=True, comment='分布式训练配置'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True, comment='超时时间(秒)'),
        sa.Column('max_retries', sa.Integer(), nullable=False, comment='最大重试次数'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['job_id'], ['training_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )
    op.create_index(op.f('ix_training_job_configs_id'), 'training_job_configs', ['id'], unique=False)

    # 创建training_job_metrics表
    op.create_table(
        'training_job_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False, comment='训练任务ID'),
        sa.Column('epoch', sa.Integer(), nullable=True, comment='训练轮次'),
        sa.Column('step', sa.Integer(), nullable=False, comment='训练步数'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, comment='记录时间'),
        sa.Column('metrics', sa.JSON(), nullable=False, comment='指标数据'),
        sa.Column('loss', sa.String(length=50), nullable=True, comment='损失值'),
        sa.Column('accuracy', sa.String(length=50), nullable=True, comment='准确率'),
        sa.Column('learning_rate', sa.String(length=50), nullable=True, comment='学习率'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['job_id'], ['training_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_training_job_metrics_id'), 'training_job_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_training_job_metrics_job_id'), 'training_job_metrics', ['job_id'], unique=False)

    # checkpointstoragetype枚举会由SQLAlchemy自动创建

    # 创建checkpoints表
    op.create_table(
        'checkpoints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False, comment='训练任务ID'),
        sa.Column('step', sa.Integer(), nullable=False, comment='训练步数'),
        sa.Column('epoch', sa.Integer(), nullable=True, comment='训练轮次'),
        sa.Column('storage_path', sa.String(length=500), nullable=False, comment='存储路径'),
        sa.Column('storage_type', postgresql.ENUM('LOCAL', 'FSX', 'S3', name='checkpointstoragetype'), nullable=False, comment='存储类型'),
        sa.Column('size_bytes', sa.Integer(), nullable=False, comment='文件大小(字节)'),
        sa.Column('checkpoint_metadata', sa.JSON(), nullable=True, comment='检查点元数据'),
        sa.Column('checkpoint_metrics', sa.JSON(), nullable=True, comment='训练指标快照'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['job_id'], ['training_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checkpoints_id'), 'checkpoints', ['id'], unique=False)
    op.create_index(op.f('ix_checkpoints_job_id'), 'checkpoints', ['job_id'], unique=False)


def downgrade() -> None:
    """删除训练任务相关表"""

    # 删除checkpoints表
    op.drop_index(op.f('ix_checkpoints_job_id'), table_name='checkpoints')
    op.drop_index(op.f('ix_checkpoints_id'), table_name='checkpoints')
    op.drop_table('checkpoints')
    op.execute('DROP TYPE IF EXISTS checkpointstoragetype')

    op.drop_index(op.f('ix_training_job_metrics_job_id'), table_name='training_job_metrics')
    op.drop_index(op.f('ix_training_job_metrics_id'), table_name='training_job_metrics')
    op.drop_table('training_job_metrics')

    op.drop_index(op.f('ix_training_job_configs_id'), table_name='training_job_configs')
    op.drop_table('training_job_configs')

    op.drop_index(op.f('ix_training_jobs_id'), table_name='training_jobs')
    op.drop_table('training_jobs')

    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS frameworktype')
    op.execute('DROP TYPE IF EXISTS trainingjobtype')
    op.execute('DROP TYPE IF EXISTS trainingjobstatus')
