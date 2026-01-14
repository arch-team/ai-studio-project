"""create core tables (users, resource_quotas, resource_limit_configs, audit_logs, development_spaces)

Revision ID: 206d5baf77c1
Revises:
Create Date: 2026-01-14 22:10:56.157123

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "206d5baf77c1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create resource_quotas table first (no FK dependencies)
    op.create_table(
        "resource_quotas",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="配额ID"),
        sa.Column("name", sa.String(length=128), nullable=False, comment="配额名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="配额描述"),
        sa.Column(
            "quota_type",
            sa.Enum("USER", "TEAM", "PROJECT", name="quotatype"),
            nullable=False,
            comment="配额类型",
        ),
        sa.Column("max_cpu_cores", sa.Integer(), nullable=False, comment="最大CPU核心数"),
        sa.Column("reserved_cpu_cores", sa.Integer(), nullable=False, comment="预留CPU核心数"),
        sa.Column("max_gpu_count", sa.Integer(), nullable=False, comment="最大GPU数量"),
        sa.Column("reserved_gpu_count", sa.Integer(), nullable=False, comment="预留GPU数量"),
        sa.Column("gpu_types", mysql.JSON(), nullable=True, comment="允许的GPU类型列表"),
        sa.Column("max_memory_gb", sa.Integer(), nullable=False, comment="最大内存(GB)"),
        sa.Column("reserved_memory_gb", sa.Integer(), nullable=False, comment="预留内存(GB)"),
        sa.Column("max_storage_gb", sa.Integer(), nullable=True, comment="最大存储空间(GB)"),
        sa.Column("max_concurrent_jobs", sa.Integer(), nullable=False, comment="最大并发训练任务数"),
        sa.Column("max_total_jobs", sa.Integer(), nullable=True, comment="总训练任务数限制"),
        sa.Column("max_spot_instances", sa.Integer(), nullable=False, comment="最大Spot实例数"),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "SUSPENDED", "EXPIRED", name="quotastatus"),
            nullable=False,
            comment="配额状态",
        ),
        sa.Column(
            "valid_from",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="生效时间",
        ),
        sa.Column("valid_until", sa.DateTime(), nullable=True, comment="过期时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人用户ID"),
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
        sa.UniqueConstraint("name"),
        comment="资源配额表",
    )
    op.create_index(op.f("ix_resource_quotas_name"), "resource_quotas", ["name"], unique=True)
    op.create_index(op.f("ix_resource_quotas_quota_type"), "resource_quotas", ["quota_type"], unique=False)
    op.create_index(op.f("ix_resource_quotas_status"), "resource_quotas", ["status"], unique=False)

    # Create users table (depends on resource_quotas)
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="用户ID"),
        sa.Column("username", sa.String(length=64), nullable=False, comment="用户名(IAM用户名)"),
        sa.Column("email", sa.String(length=255), nullable=False, comment="邮箱地址"),
        sa.Column("display_name", sa.String(length=128), nullable=True, comment="显示名称"),
        sa.Column(
            "iam_identity_id", sa.String(length=255), nullable=True, comment="AWS IAM Identity Center用户ID"
        ),
        sa.Column("iam_groups", mysql.JSON(), nullable=True, comment="IAM用户组列表"),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", "SUSPENDED", name="userstatus"),
            nullable=False,
            comment="用户状态",
        ),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "PROJECT_MANAGER", "ENGINEER", "VIEWER", name="userrole"),
            nullable=False,
            comment="用户角色",
        ),
        sa.Column("resource_quota_id", sa.BigInteger(), nullable=True, comment="关联的资源配额ID"),
        sa.Column("last_login_at", sa.DateTime(), nullable=True, comment="最后登录时间"),
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
        sa.ForeignKeyConstraint(
            ["resource_quota_id"], ["resource_quotas.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("iam_identity_id"),
        sa.UniqueConstraint("username"),
        comment="用户表",
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_resource_quota_id"), "users", ["resource_quota_id"], unique=False)
    op.create_index(op.f("ix_users_status"), "users", ["status"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Add FK from resource_quotas.created_by to users.id (circular reference)
    op.create_foreign_key(
        "fk_resource_quotas_created_by_users",
        "resource_quotas",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create resource_limit_configs table
    op.create_table(
        "resource_limit_configs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="配置ID"),
        sa.Column("config_name", sa.String(length=128), nullable=False, comment="配置名称"),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "PROJECT_MANAGER", "ENGINEER", "VIEWER", name="limitrole"),
            nullable=False,
            comment="适用角色",
        ),
        sa.Column("project_id", sa.BigInteger(), nullable=True, comment="项目ID(空表示全局配置)"),
        sa.Column("max_gpu_per_job", sa.Integer(), nullable=False, comment="单任务最大GPU数"),
        sa.Column("max_cpu_per_job", sa.Integer(), nullable=False, comment="单任务最大CPU核心数"),
        sa.Column("max_memory_gb_per_job", sa.Integer(), nullable=False, comment="单任务最大内存(GB)"),
        sa.Column("max_storage_gb_per_job", sa.Integer(), nullable=False, comment="单任务最大存储(GB)"),
        sa.Column("max_nodes_per_job", sa.Integer(), nullable=False, comment="单任务最大节点数"),
        sa.Column(
            "priority_default",
            sa.Enum("HIGH", "MEDIUM", "LOW", name="prioritydefault"),
            nullable=False,
            comment="默认优先级",
        ),
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
        comment="资源限制配置表",
    )
    op.create_index(
        op.f("ix_resource_limit_configs_config_name"), "resource_limit_configs", ["config_name"], unique=False
    )
    op.create_index(op.f("ix_resource_limit_configs_project_id"), "resource_limit_configs", ["project_id"], unique=False)
    op.create_index(op.f("ix_resource_limit_configs_role"), "resource_limit_configs", ["role"], unique=False)

    # Create audit_logs table (depends on users)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="审计日志ID"),
        sa.Column("user_id", sa.BigInteger(), nullable=True, comment="用户ID"),
        sa.Column(
            "operation_type",
            sa.Enum("CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", name="operationtype"),
            nullable=False,
            comment="操作类型",
        ),
        sa.Column(
            "resource_type",
            sa.Enum("TRAINING_JOB", "DATASET", "MODEL", "USER", "QUOTA", "SPACE", name="resourcetype"),
            nullable=False,
            comment="资源类型",
        ),
        sa.Column("resource_id", sa.String(length=64), nullable=True, comment="资源ID"),
        sa.Column("request_data", mysql.JSON(), nullable=True, comment="请求数据"),
        sa.Column("response_data", mysql.JSON(), nullable=True, comment="响应数据"),
        sa.Column("ip_address", sa.String(length=45), nullable=True, comment="IP地址"),
        sa.Column("user_agent", sa.Text(), nullable=True, comment="User-Agent"),
        sa.Column(
            "status",
            sa.Enum("SUCCESS", "FAILED", name="auditstatus"),
            nullable=False,
            comment="操作状态",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False, comment="过期时间(90天后)"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        comment="审计日志表",
    )
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_expires_at"), "audit_logs", ["expires_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_operation_type"), "audit_logs", ["operation_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_status"), "audit_logs", ["status"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)

    # Create development_spaces table (depends on users)
    op.create_table(
        "development_spaces",
        sa.Column("id", mysql.CHAR(length=36), nullable=False, comment="空间ID(UUID)"),
        sa.Column("space_name", sa.String(length=255), nullable=False, comment="空间名称"),
        sa.Column("owner_id", sa.BigInteger(), nullable=False, comment="所有者用户ID"),
        sa.Column(
            "instance_type",
            sa.Enum(
                "ML_T3_MEDIUM",
                "ML_T3_LARGE",
                "ML_G4DN_XLARGE",
                "ML_G5_XLARGE",
                "ML_G5_2XLARGE",
                name="spaceinstancetype",
            ),
            nullable=False,
            comment="实例类型",
        ),
        sa.Column(
            "space_type",
            sa.Enum("JUPYTER", "VSCODE", "RSTUDIO", name="spacetype"),
            nullable=False,
            comment="空间类型",
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RUNNING", "STOPPED", "FAILED", "DELETED", name="spacestatus"),
            nullable=False,
            comment="空间状态",
        ),
        sa.Column("storage_size_gb", sa.Integer(), nullable=False, comment="存储大小(GB)"),
        sa.Column("lifecycle_config_arn", sa.String(length=512), nullable=True, comment="Lifecycle配置ARN"),
        sa.Column("sagemaker_space_arn", sa.String(length=512), nullable=True, comment="SageMaker Space ARN"),
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
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="软删除时间"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sagemaker_space_arn"),
        comment="开发空间表",
    )
    op.create_index(op.f("ix_development_spaces_owner_id"), "development_spaces", ["owner_id"], unique=False)
    op.create_index(op.f("ix_development_spaces_space_name"), "development_spaces", ["space_name"], unique=False)
    op.create_index(op.f("ix_development_spaces_status"), "development_spaces", ["status"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index(op.f("ix_development_spaces_status"), table_name="development_spaces")
    op.drop_index(op.f("ix_development_spaces_space_name"), table_name="development_spaces")
    op.drop_index(op.f("ix_development_spaces_owner_id"), table_name="development_spaces")
    op.drop_table("development_spaces")

    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_status"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_operation_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_expires_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_resource_limit_configs_role"), table_name="resource_limit_configs")
    op.drop_index(op.f("ix_resource_limit_configs_project_id"), table_name="resource_limit_configs")
    op.drop_index(op.f("ix_resource_limit_configs_config_name"), table_name="resource_limit_configs")
    op.drop_table("resource_limit_configs")

    op.drop_constraint("fk_resource_quotas_created_by_users", "resource_quotas", type_="foreignkey")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_status"), table_name="users")
    op.drop_index(op.f("ix_users_resource_quota_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_resource_quotas_status"), table_name="resource_quotas")
    op.drop_index(op.f("ix_resource_quotas_quota_type"), table_name="resource_quotas")
    op.drop_index(op.f("ix_resource_quotas_name"), table_name="resource_quotas")
    op.drop_table("resource_quotas")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS spacestatus")
    op.execute("DROP TYPE IF EXISTS spacetype")
    op.execute("DROP TYPE IF EXISTS spaceinstancetype")
    op.execute("DROP TYPE IF EXISTS auditstatus")
    op.execute("DROP TYPE IF EXISTS resourcetype")
    op.execute("DROP TYPE IF EXISTS operationtype")
    op.execute("DROP TYPE IF EXISTS prioritydefault")
    op.execute("DROP TYPE IF EXISTS limitrole")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS userstatus")
    op.execute("DROP TYPE IF EXISTS quotastatus")
    op.execute("DROP TYPE IF EXISTS quotatype")
