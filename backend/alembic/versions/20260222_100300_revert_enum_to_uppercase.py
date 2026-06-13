"""revert enum values to uppercase for SQLAlchemy 2.0 compatibility

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-02-22 10:03:00.000000

SQLAlchemy 2.0+ stores Python Enum .name (UPPERCASE) by default.
Previous migration incorrectly lowercased DB enum values.
This reverts all enum values to uppercase and adds PAUSE/RESUME/CANCEL.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "g7h8i9j0k1l2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE users MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE users SET status = UPPER(status)")
    op.execute("ALTER TABLE users MODIFY COLUMN status ENUM('ACTIVE','INACTIVE','SUSPENDED') NOT NULL")

    op.execute("ALTER TABLE users MODIFY COLUMN role VARCHAR(30) NOT NULL")
    op.execute("UPDATE users SET role = UPPER(role)")
    op.execute("ALTER TABLE users MODIFY COLUMN role ENUM('ADMIN','PROJECT_MANAGER','ENGINEER','VIEWER') NOT NULL")

    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN quota_type VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_quotas SET quota_type = UPPER(quota_type)")
    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN quota_type ENUM('USER','TEAM','PROJECT') NOT NULL")

    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_quotas SET status = UPPER(status)")
    op.execute("ALTER TABLE resource_quotas MODIFY COLUMN status ENUM('ACTIVE','SUSPENDED','EXPIRED') NOT NULL")

    op.execute("ALTER TABLE resource_limit_configs MODIFY COLUMN role VARCHAR(30) NOT NULL")
    op.execute("UPDATE resource_limit_configs SET role = UPPER(role)")
    op.execute(
        "ALTER TABLE resource_limit_configs MODIFY COLUMN role ENUM('ADMIN','PROJECT_MANAGER','ENGINEER','VIEWER') NOT NULL"
    )

    op.execute("ALTER TABLE resource_limit_configs MODIFY COLUMN priority_default VARCHAR(20) NOT NULL")
    op.execute("UPDATE resource_limit_configs SET priority_default = UPPER(priority_default)")
    op.execute("ALTER TABLE resource_limit_configs MODIFY COLUMN priority_default ENUM('HIGH','MEDIUM','LOW') NOT NULL")

    op.execute("ALTER TABLE audit_logs MODIFY COLUMN operation_type VARCHAR(20) NOT NULL")
    op.execute("UPDATE audit_logs SET operation_type = UPPER(operation_type)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN operation_type ENUM('CREATE','UPDATE','DELETE','LOGIN','LOGOUT','PAUSE','RESUME','CANCEL') NOT NULL"
    )

    op.execute("ALTER TABLE audit_logs MODIFY COLUMN resource_type VARCHAR(30) NOT NULL")
    op.execute("UPDATE audit_logs SET resource_type = UPPER(resource_type)")
    op.execute(
        "ALTER TABLE audit_logs MODIFY COLUMN resource_type ENUM('TRAINING_JOB','DATASET','MODEL','USER','QUOTA','SPACE') NOT NULL"
    )

    op.execute("ALTER TABLE audit_logs MODIFY COLUMN status VARCHAR(20) NOT NULL")
    op.execute("UPDATE audit_logs SET status = UPPER(status)")
    op.execute("ALTER TABLE audit_logs MODIFY COLUMN status ENUM('SUCCESS','FAILED') NOT NULL")


def downgrade() -> None:
    for table, col, vals in [
        ("users", "status", "'active','inactive','suspended'"),
        ("users", "role", "'admin','project_manager','engineer','viewer'"),
        ("resource_quotas", "quota_type", "'user','team','project'"),
        ("resource_quotas", "status", "'active','suspended','expired'"),
        ("resource_limit_configs", "role", "'admin','project_manager','engineer','viewer'"),
        ("resource_limit_configs", "priority_default", "'high','medium','low'"),
        ("audit_logs", "operation_type", "'create','update','delete','login','logout','pause','resume','cancel'"),
        ("audit_logs", "resource_type", "'training_job','dataset','model','user','quota','space'"),
        ("audit_logs", "status", "'success','failed'"),
    ]:
        op.execute(f"ALTER TABLE {table} MODIFY COLUMN {col} VARCHAR(30) NOT NULL")
        op.execute(f"UPDATE {table} SET {col} = LOWER({col})")
        op.execute(f"ALTER TABLE {table} MODIFY COLUMN {col} ENUM({vals}) NOT NULL")
