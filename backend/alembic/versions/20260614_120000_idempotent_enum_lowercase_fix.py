"""idempotent enum lowercase fix (covers auth_type omitted by h8i9j0k1l2m3)

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-06-14 12:00:00.000000

背景与必要性
============
commit 8777581 将 auth/quotas/audit 共 10 个 ORM enum 列改用 ``lowercase_enum``
(按小写 .value 读写)，并新增迁移 h8i9j0k1l2m3 把对应 DB 列小写化。但在 dev 等
环境观察到:

1. **alembic_version 记录与真实 schema 脱节** —— 版本号已越过 h8i9j0k1l2m3，
   但 DB 列定义仍是大写 ``ENUM('ACTIVE',...)``、数据仍是大写。说明 h8 的 DDL
   从未在该环境真正执行(库由旧 dump 重建或被 stamp 推进版本号)。直接
   ``alembic upgrade head`` 无法修复 —— alembic 认为 h8 早已执行，不会重跑。
2. **h8i9j0k1l2m3 遗漏了 users.auth_type** —— 即便补跑 h8，登录读 auth_type
   仍会抛 LookupError → 500。

本迁移以**幂等**方式收口:逐列检测 ``information_schema`` 中 COLUMN_TYPE 是否
仍为大写值集，仅对仍大写的列执行 VARCHAR→LOWER()→小写 ENUM 三步转换。
对已小写的环境为 no-op，可安全重复执行，并补齐 auth_type。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "k1l2m3n4o5p6"
down_revision: str | None = "j0k1l2m3n4o5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# (table, column, varchar_width, 小写 ENUM 值集)
# 顺序与 lowercase_enum 列清单一致；含 h8i9j0k1l2m3 遗漏的 users.auth_type。
_ENUM_COLUMNS: list[tuple[str, str, int, str]] = [
    ("users", "status", 20, "'active','inactive','suspended'"),
    ("users", "role", 30, "'admin','project_manager','engineer','viewer'"),
    ("users", "auth_type", 20, "'sso','local'"),  # h8 遗漏，本迁移补齐
    ("resource_quotas", "quota_type", 20, "'user','team','project'"),
    ("resource_quotas", "status", 20, "'active','suspended','expired'"),
    ("resource_limit_configs", "role", 30, "'admin','project_manager','engineer','viewer'"),
    ("resource_limit_configs", "priority_default", 20, "'high','medium','low'"),
    (
        "audit_logs",
        "operation_type",
        20,
        "'create','update','delete','login','logout','pause','resume','cancel'",
    ),
    (
        "audit_logs",
        "resource_type",
        30,
        "'training_job','dataset','model','user','quota','space'",
    ),
    ("audit_logs", "status", 20, "'success','failed'"),
]


def _column_type(table: str, column: str) -> str | None:
    """读取列在当前库的 COLUMN_TYPE 定义(如 ``enum('ACTIVE',...)``)。"""
    conn = op.get_bind()
    row = conn.exec_driver_sql(
        "SELECT COLUMN_TYPE FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
        (table, column),
    ).fetchone()
    return row[0] if row else None


def _needs_lowercasing(column_type: str | None) -> bool:
    """判断列定义是否仍含大写字母(即尚未小写化)。

    小写 ENUM 定义形如 ``enum('active',...)`` 不含大写字母；存量大写定义
    ``enum('ACTIVE',...)`` 含大写。以"值集内是否出现大写字母"为判据，
    避免误判已小写的环境。
    """
    if not column_type:
        return False
    # 去掉 "enum(" 外壳前缀后，看括号内是否出现大写字母
    inner = column_type[column_type.find("(") + 1 :] if "(" in column_type else column_type
    return any(ch.isupper() for ch in inner)


def upgrade() -> None:
    for table, column, width, lower_vals in _ENUM_COLUMNS:
        col_type = _column_type(table, column)
        if col_type is None:
            # 该环境无此列(如此前迁移未落地)，跳过
            continue
        if not _needs_lowercasing(col_type):
            # 已是小写，no-op
            continue
        # 三步安全转换：放宽为 VARCHAR → 数据小写化 → 收回小写 ENUM
        op.execute(f"ALTER TABLE {table} MODIFY COLUMN {column} VARCHAR({width}) NOT NULL")
        op.execute(f"UPDATE {table} SET {column} = LOWER({column})")
        op.execute(f"ALTER TABLE {table} MODIFY COLUMN {column} ENUM({lower_vals}) NOT NULL")


def downgrade() -> None:
    # 仅对仍为小写的列回退为大写 ENUM(同样幂等)。
    upper_map: dict[tuple[str, str], str] = {
        ("users", "status"): "'ACTIVE','INACTIVE','SUSPENDED'",
        ("users", "role"): "'ADMIN','PROJECT_MANAGER','ENGINEER','VIEWER'",
        ("users", "auth_type"): "'SSO','LOCAL'",
        ("resource_quotas", "quota_type"): "'USER','TEAM','PROJECT'",
        ("resource_quotas", "status"): "'ACTIVE','SUSPENDED','EXPIRED'",
        ("resource_limit_configs", "role"): "'ADMIN','PROJECT_MANAGER','ENGINEER','VIEWER'",
        ("resource_limit_configs", "priority_default"): "'HIGH','MEDIUM','LOW'",
        ("audit_logs", "operation_type"): "'CREATE','UPDATE','DELETE','LOGIN','LOGOUT','PAUSE','RESUME','CANCEL'",
        ("audit_logs", "resource_type"): "'TRAINING_JOB','DATASET','MODEL','USER','QUOTA','SPACE'",
        ("audit_logs", "status"): "'SUCCESS','FAILED'",
    }
    for table, column, width, _ in _ENUM_COLUMNS:
        col_type = _column_type(table, column)
        if col_type is None or _needs_lowercasing(col_type):
            continue  # 列不存在或已是大写，跳过
        upper_vals = upper_map[(table, column)]
        op.execute(f"ALTER TABLE {table} MODIFY COLUMN {column} VARCHAR({width}) NOT NULL")
        op.execute(f"UPDATE {table} SET {column} = UPPER({column})")
        op.execute(f"ALTER TABLE {table} MODIFY COLUMN {column} ENUM({upper_vals}) NOT NULL")
