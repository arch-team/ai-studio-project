"""fix enum case mismatch and add audit operation types

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-22 10:01:00.000000

Fixes enum values in database to match Python Domain Value Objects (lowercase).
The original migration (206d5baf77c1) used uppercase enum values (e.g. "ACTIVE"),
but the Python Enum classes use lowercase values (e.g. "active").

Also adds missing audit operation types: pause, resume, cancel.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # 1. users.status: ACTIVE/INACTIVE/SUSPENDED -> active/inactive/suspended
    # ============================================================
    op.execute("ALTER TABLE users MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE users SET status = LOWER(status)")
    op.execute(
        "ALTER TABLE users MODIFY COLUMN status "
        "ENUM('active','inactive','suspended') NOT NULL COMMENT '用户状态'"
    )

    # ============================================================
    # 2. users.role: ADMIN/PROJECT_MANAGER/ENGINEER/VIEWER -> lowercase
    # ============================================================
    op.execute("ALTER TABLE users MODIFY COLUMN role VARCHAR(30) NOT NULL")
    op.execute("UPDATE users SET role = LOWER(role)")
    op.execute(
        "ALTER TABLE users MODIFY COLUMN role "
        "ENUM('admin','project_manager','engineer','viewer') NOT NULL COMMENT '用户角色'"
    )

    # ============================================================
    # 3. resource_quotas.quota_type: USER/TEAM/PROJECT -> lowercase
    # ============================================================
    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN quota_type VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_quotas SET quota_type = LOWER(quota_type)")
    op.execute(
        "ALTER TABLE resource_quotas MODIFY COLUMN quota_type "
        "ENUM('user','team','project') NOT NULL COMMENT '配额类型'"
    )

    # ============================================================
    # 4. resource_quotas.status: ACTIVE/SUSPENDED/EXPIRED -> lowercase
    # ============================================================
    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_quotas SET status = LOWER(status)")
    op.execute(
        "ALTER TABLE resource_quotas MODIFY COLUMN status "
        "ENUM('active','suspended','expired') NOT NULL COMMENT '配额状态'"
    )

    # ============================================================
    # 5. resource_limit_configs.role: ADMIN/.../VIEWER -> lowercase
    # ============================================================
    op.execute("ALTER TABLE resource_limit_configs MODIFY COLUMN role VARCHAR(30) NOT NULL")
    op.execute("UPDATE resource_limit_configs SET role = LOWER(role)")
    op.execute(
        "ALTER TABLE resource_limit_configs MODIFY COLUMN role "
        "ENUM('admin','project_manager','engineer','viewer') NOT NULL COMMENT '适用角色'"
    )

    # ============================================================
    # 6. resource_limit_configs.priority_default: HIGH/MEDIUM/LOW -> lowercase
    # ============================================================
    op.execute("ALTER TABLE resource_limit_configs MODIFY COLUMN priority_default VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_limit_configs SET priority_default = LOWER(priority_default)")
    op.execute(
        "ALTER TABLE resource_limit_configs MODIFY COLUMN priority_default "
        "ENUM('high','medium','low') NOT NULL COMMENT '默认优先级'"
    )

    # ============================================================
    # 7. audit_logs.operation_type: uppercase -> lowercase + add pause/resume/cancel
    # ============================================================
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN operation_type VARCHAR(20) NOT NULL")
    op.execute("UPDATE audit_logs SET operation_type = LOWER(operation_type)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN operation_type "
        "ENUM('create','update','delete','login','logout','pause','resume','cancel') "
        "NOT NULL COMMENT '操作类型'"
    )

    # ============================================================
    # 8. audit_logs.resource_type: TRAINING_JOB -> training_job etc.
    # ============================================================
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN resource_type VARCHAR(30) NOT NULL")
    op.execute("UPDATE audit_logs SET resource_type = LOWER(resource_type)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN resource_type "
        "ENUM('training_job','dataset','model','user','quota','space') "
        "NOT NULL COMMENT '资源类型'"
    )

    # ============================================================
    # 9. audit_logs.status: SUCCESS/FAILED -> lowercase
    # ============================================================
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE audit_logs SET status = LOWER(status)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN status "
        "ENUM('success','failed') NOT NULL COMMENT '操作状态'"
    )


def downgrade() -> None:
    # Reverse: lowercase -> uppercase for all enum columns

    # 9. audit_logs.status
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE audit_logs SET status = UPPER(status)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN status "
        "ENUM('SUCCESS','FAILED') NOT NULL COMMENT '操作状态'"
    )

    # 8. audit_logs.resource_type
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN resource_type VARCHAR(30) NOT NULL")
    op.execute("UPDATE audit_logs SET resource_type = UPPER(resource_type)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN resource_type "
        "ENUM('TRAINING_JOB','DATASET','MODEL','USER','QUOTA','SPACE') "
        "NOT NULL COMMENT '资源类型'"
    )

    # 7. audit_logs.operation_type (remove pause/resume/cancel)
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN operation_type VARCHAR(20) NOT NULL")
    op.execute("DELETE FROM audit_logs WHERE operation_type IN ('pause','resume','cancel')")
    op.execute("UPDATE audit_logs SET operation_type = UPPER(operation_type)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN operation_type "
        "ENUM('CREATE','UPDATE','DELETE','LOGIN','LOGOUT') NOT NULL COMMENT '操作类型'"
    )

    # 6. resource_limit_configs.priority_default
    op.execute("ALTER TABLE resource_limit_configs MODIFY COLUMN priority_default VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_limit_configs SET priority_default = UPPER(priority_default)")
    op.execute(
        "ALTER TABLE resource_limit_configs MODIFY COLUMN priority_default "
        "ENUM('HIGH','MEDIUM','LOW') NOT NULL COMMENT '默认优先级'"
    )

    # 5. resource_limit_configs.role
    op.execute("ALTER TABLE resource_limit_configs MODIFY COLUMN role VARCHAR(30) NOT NULL")
    op.execute("UPDATE resource_limit_configs SET role = UPPER(role)")
    op.execute(
        "ALTER TABLE resource_limit_configs MODIFY COLUMN role "
        "ENUM('ADMIN','PROJECT_MANAGER','ENGINEER','VIEWER') NOT NULL COMMENT '适用角色'"
    )

    # 4. resource_quotas.status
    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_quotas SET status = UPPER(status)")
    op.execute(
        "ALTER TABLE resource_quotas MODIFY COLUMN status "
        "ENUM('ACTIVE','SUSPENDED','EXPIRED') NOT NULL COMMENT '配额状态'"
    )

    # 3. resource_quotas.quota_type
    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN quota_type VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_quotas SET quota_type = UPPER(quota_type)")
    op.execute(
        "ALTER TABLE resource_quotas MODIFY COLUMN quota_type "
        "ENUM('USER','TEAM','PROJECT') NOT NULL COMMENT '配额类型'"
    )

    # 2. users.role
    op.execute("ALTER TABLE users MODIFY COLUMN role VARCHAR(30) NOT NULL")
    op.execute("UPDATE users SET role = UPPER(role)")
    op.execute(
        "ALTER TABLE users MODIFY COLUMN role "
        "ENUM('ADMIN','PROJECT_MANAGER','ENGINEER','VIEWER') NOT NULL COMMENT '用户角色'"
    )

    # 1. users.status
    op.execute("ALTER TABLE users MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE users SET status = UPPER(status)")
    op.execute(
        "ALTER TABLE users MODIFY COLUMN status "
        "ENUM('ACTIVE','INACTIVE','SUSPENDED') NOT NULL COMMENT '用户状态'"
    )
