"""Initial migration: users, teams, projects

Revision ID: 001
Revises:
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建用户、团队、项目表"""

    # 创建users表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False, comment='用户名'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='邮箱地址'),
        sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='密码哈希'),
        sa.Column('full_name', sa.String(length=100), nullable=True, comment='全名'),
        sa.Column('role', sa.Enum('ADMIN', 'PROJECT_MANAGER', 'ALGORITHM_ENGINEER', 'DATA_ENGINEER', 'VIEWER', name='userrole'), nullable=False, comment='用户角色'),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'SUSPENDED', name='userstatus'), nullable=False, comment='用户状态'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否激活'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, comment='是否超级用户'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='删除时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 创建teams表
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='团队名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='团队描述'),
        sa.Column('owner_id', sa.Integer(), nullable=False, comment='所有者ID'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='删除时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)
    op.create_index(op.f('ix_teams_name'), 'teams', ['name'], unique=True)

    # 创建team_members关联表
    op.create_table(
        'team_members',
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('team_id', 'user_id')
    )

    # 创建projects表
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='项目名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='项目描述'),
        sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', 'SUSPENDED', name='projectstatus'), nullable=False, comment='项目状态'),
        sa.Column('owner_id', sa.Integer(), nullable=False, comment='所有者ID'),
        sa.Column('team_id', sa.Integer(), nullable=False, comment='团队ID'),
        sa.Column('namespace', sa.String(length=63), nullable=False, comment='Kubernetes命名空间'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='删除时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    op.create_index(op.f('ix_projects_namespace'), 'projects', ['namespace'], unique=True)


def downgrade() -> None:
    """删除用户、团队、项目表"""

    op.drop_index(op.f('ix_projects_namespace'), table_name='projects')
    op.drop_index(op.f('ix_projects_name'), table_name='projects')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')

    op.drop_table('team_members')

    op.drop_index(op.f('ix_teams_name'), table_name='teams')
    op.drop_index(op.f('ix_teams_id'), table_name='teams')
    op.drop_table('teams')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS projectstatus')
    op.execute('DROP TYPE IF EXISTS userstatus')
    op.execute('DROP TYPE IF EXISTS userrole')
