"""fix enum values to match Python Enum .value (lowercase)

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-02-22 10:04:00.000000

SQLAlchemy 2.0+ with Python Enum stores .value (not .name) by default.
Previous migration incorrectly assumed .name (uppercase) was used.
This reverts all enum values to lowercase to match Python Enum .value definitions.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users.status: ACTIVE/INACTIVE/SUSPENDED -> active/inactive/suspended
    op.execute("ALTER TABLE users MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE users SET status = LOWER(status)")
    op.execute(
        "ALTER TABLE users MODIFY COLUMN status "
        "ENUM('active','inactive','suspended') NOT NULL"
    )

    # users.role: ADMIN/PROJECT_MANAGER/ENGINEER/VIEWER -> lowercase
    op.execute("ALTER TABLE users MODIFY COLUMN role VARCHAR(30) NOT NULL")
    op.execute("UPDATE users SET role = LOWER(role)")
    op.execute(
        "ALTER TABLE users MODIFY COLUMN role "
        "ENUM('admin','project_manager','engineer','viewer') NOT NULL"
    )

    # resource_quotas.quota_type: USER/TEAM/PROJECT -> lowercase
    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN quota_type VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_quotas SET quota_type = LOWER(quota_type)")
    op.execute(
        "ALTER TABLE resource_quotas MODIFY COLUMN quota_type "
        "ENUM('user','team','project') NOT NULL"
    )

    # resource_quotas.status: ACTIVE/SUSPENDED/EXPIRED -> lowercase
    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_quotas SET status = LOWER(status)")
    op.execute(
        "ALTER TABLE resource_quotas MODIFY COLUMN status "
        "ENUM('active','suspended','expired') NOT NULL"
    )

    # resource_limit_configs.role: ADMIN/PROJECT_MANAGER/ENGINEER/VIEWER -> lowercase
    op.execute("ALTER TABLE resource_limit_configs MODIFY COLUMN role VARCHAR(30) NOT NULL")
    op.execute("UPDATE resource_limit_configs SET role = LOWER(role)")
    op.execute(
        "ALTER TABLE resource_limit_configs MODIFY COLUMN role "
        "ENUM('admin','project_manager','engineer','viewer') NOT NULL"
    )

    # resource_limit_configs.priority_default: HIGH/MEDIUM/LOW -> lowercase
    op.execute(
        "ALTER TABLE resource_limit_configs MODIFY COLUMN priority_default VARCHAR(20) NOT NULL"
    )
    op.execute("UPDATE resource_limit_configs SET priority_default = LOWER(priority_default)")
    op.execute(
        "ALTER TABLE resource_limit_configs MODIFY COLUMN priority_default "
        "ENUM('high','medium','low') NOT NULL"
    )

    # audit_logs.operation_type -> lowercase
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN operation_type VARCHAR(20) NOT NULL")
    op.execute("UPDATE audit_logs SET operation_type = LOWER(operation_type)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN operation_type "
        "ENUM('create','update','delete','login','logout','pause','resume','cancel') NOT NULL"
    )

    # audit_logs.resource_type -> lowercase
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN resource_type VARCHAR(30) NOT NULL")
    op.execute("UPDATE audit_logs SET resource_type = LOWER(resource_type)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN resource_type "
        "ENUM('training_job','dataset','model','user','quota','space') NOT NULL"
    )

    # audit_logs.status -> lowercase
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE audit_logs SET status = LOWER(status)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN status "
        "ENUM('success','failed') NOT NULL"
    )


def downgrade() -> None:
    for table, col, vals in [
        ("users", "status", "'ACTIVE','INACTIVE','SUSPENDED'"),
        ("users", "role", "'ADMIN','PROJECT_MANAGER','ENGINEER','VIEWER'"),
        ("resource_quotas", "quota_type", "'USER','TEAM','PROJECT'"),
        ("resource_quotas", "status", "'ACTIVE','SUSPENDED','EXPIRED'"),
        ("resource_limit_configs", "role", "'ADMIN','PROJECT_MANAGER','ENGINEER','VIEWER'"),
        ("resource_limit_configs", "priority_default", "'HIGH','MEDIUM','LOW'"),
        (
            "audit_logs",
            "operation_type",
            "'CREATE','UPDATE','DELETE','LOGIN','LOGOUT','PAUSE','RESUME','CANCEL'",
        ),
        (
            "audit_logs",
            "resource_type",
            "'TRAINING_JOB','DATASET','MODEL','USER','QUOTA','SPACE'",
        ),
        ("audit_logs", "status", "'SUCCESS','FAILED'"),
    ]:
        op.execute(f"ALTER TABLE {table} MODIFY COLUMN {col} VARCHAR(30) NOT NULL")
        op.execute(f"UPDATE {table} SET {col} = UPPER({col})")
        op.execute(f"ALTER TABLE {table} MODIFY COLUMN {col} ENUM({vals}) NOT NULL")
