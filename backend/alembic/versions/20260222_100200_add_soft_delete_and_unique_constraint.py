"""add soft delete and unique constraint to resource_limit_configs

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-22 10:02:00.000000

Changes:
1. Add deleted_at column for soft delete support
2. Add unique constraint on (role, project_id) to prevent duplicates at DB level
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 添加 deleted_at 列 (软删除支持)
    op.add_column(
        "resource_limit_configs",
        sa.Column(
            "deleted_at",
            sa.DateTime(),
            nullable=True,
            comment="软删除时间",
        ),
    )

    # 2. 添加 (role, project_id) 唯一约束
    # 注意: MySQL 中 NULL 不参与唯一约束比较，
    # 即 (admin, NULL) 和 (admin, NULL) 在 MySQL 中不会冲突。
    # 对于 project_id=NULL 的全局配置，仍需应用层做重复检查。
    op.create_unique_constraint(
        "uq_resource_limit_configs_role_project",
        "resource_limit_configs",
        ["role", "project_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_resource_limit_configs_role_project",
        "resource_limit_configs",
        type_="unique",
    )
    op.drop_column("resource_limit_configs", "deleted_at")
