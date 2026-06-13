"""架构防回归测试 - ORM Enum 列持久化大小写一致性。

背景 (Issue #3):
    SQLAlchemy ``Enum()`` 默认按成员名 (.name) 持久化/读回。当 Python Enum
    成员名 ≠ .value (典型: 名大写、值小写)、而数据库 ENUM 列定义为小写 .value 时，
    读回会抛 ``LookupError: '...' is not among the defined enum values``。
    正确做法是用 ``values_callable`` (见 src/shared/infrastructure/db_enum.py 的
    lowercase_enum) 让 SQLAlchemy 改用 .value 读写。

本测试扫描所有 ORM Enum 列，对"成员名 ≠ .value"的列强制要求设置了
values_callable —— 除非该列在白名单中 (其数据库列定义为大写成员名，
按 .name 读写本身就一致，加 values_callable 反而会破坏)。

新增一个名≠值的 Enum 列却忘记处理大小写时，本测试会失败并指明列名。
"""

from enum import Enum as PyEnum

import pytest
from sqlalchemy import Enum as SAEnum

from src.shared.infrastructure.database import Base

# 在收集映射前确保所有 ORM 模型已加载 (含未被 import_all_models 覆盖的模块)。
import_module_paths = [
    "src.modules.audit.infrastructure.models.audit_log_model",
    "src.modules.auth.infrastructure.models.user_model",
    "src.modules.auth.infrastructure.models.login_attempt_model",
    "src.modules.auth.infrastructure.models.password_history_model",
    "src.modules.datasets.infrastructure.models.dataset_model",
    "src.modules.datasets.infrastructure.models.upload_session_model",
    "src.modules.models.infrastructure.models.model_model",
    "src.modules.monitoring.infrastructure.models.hyperpod_cluster_model",
    "src.modules.quotas.infrastructure.models.resource_limit_config_model",
    "src.modules.quotas.infrastructure.models.resource_quota_model",
    "src.modules.spaces.infrastructure.models.space_model",
    "src.modules.training.infrastructure.models.checkpoint_model",
    "src.modules.training.infrastructure.models.job_template_model",
    "src.modules.training.infrastructure.models.training_job_model",
]


def _load_all_models() -> None:
    """显式 import 全部 ORM 模型文件，确保 Base.metadata 收集完整。"""
    import importlib

    for path in import_module_paths:
        importlib.import_module(path)


# 白名单: 数据库 ENUM 列定义为大写成员名 (.name) 的列。
# SQLAlchemy 默认按 .name 读写，与这些列天然一致；若误加 values_callable 反而破坏。
# 格式: (表名, 列名)
NAME_PERSISTED_ENUM_COLUMNS: set[tuple[str, str]] = {
    # spaces 模块: 迁移定义 ENUM('STUDIO','HYPERPOD') 等大写成员名 (见迁移
    # 20260613_140000 与 206d5baf77c1)，按 .name 持久化，self-consistent。
    ("development_spaces", "instance_type"),
    ("development_spaces", "space_type"),
    ("development_spaces", "backend"),
    ("development_spaces", "status"),
}


def _collect_enum_columns() -> list[tuple[str, str, type[PyEnum], bool]]:
    """收集所有 ORM Enum 列。

    返回 (表名, 列名, enum 类, 是否已设 values_callable) 列表。
    """
    _load_all_models()
    columns: list[tuple[str, str, type[PyEnum], bool]] = []
    for table_name, table in Base.metadata.tables.items():
        for col in table.columns:
            if isinstance(col.type, SAEnum) and col.type.enum_class is not None:
                columns.append((table_name, col.name, col.type.enum_class, col.type.values_callable is not None))
    return columns


class TestEnumPersistenceCompliance:
    """验证所有名≠值的 ORM Enum 列正确处理了持久化大小写。"""

    def test_name_neq_value_enum_columns_use_values_callable(self) -> None:
        """成员名 ≠ .value 的 Enum 列必须设 values_callable (除非在大写成员名白名单)。"""
        violations: list[str] = []

        for table_name, col_name, enum_cls, has_values_callable in _collect_enum_columns():
            name_equals_value = all(member.name == member.value for member in enum_cls)
            if name_equals_value:
                continue  # 名==值，按 .name 或 .value 读写等价，无需处理

            if (table_name, col_name) in NAME_PERSISTED_ENUM_COLUMNS:
                continue  # 白名单: DB 存成员名，self-consistent

            if not has_values_callable:
                violations.append(
                    f"{table_name}.{col_name} (enum={enum_cls.__name__}): "
                    f"成员名≠.value 但未设 values_callable，读回小写 DB 值会抛 LookupError。"
                    f"请用 src.shared.infrastructure.lowercase_enum 包装该列。"
                )

        assert not violations, "发现未处理大小写的 Enum 列:\n" + "\n".join(violations)

    def test_whitelist_columns_actually_exist(self) -> None:
        """白名单中的列必须真实存在 (防止表/列改名后白名单失效仍误放行)。"""
        all_columns = {(t, c) for t, c, _, _ in _collect_enum_columns()}
        missing = NAME_PERSISTED_ENUM_COLUMNS - all_columns
        assert not missing, f"白名单包含不存在的列 (需更新白名单): {missing}"

    @pytest.mark.parametrize(
        "table_name,col_name",
        sorted(NAME_PERSISTED_ENUM_COLUMNS),
    )
    def test_whitelisted_columns_are_name_neq_value(self, table_name: str, col_name: str) -> None:
        """白名单列应确实是名≠值 (名==值的列无需进白名单，进了说明理解有误)。"""
        enum_map = {(t, c): ec for t, c, ec, _ in _collect_enum_columns()}
        enum_cls = enum_map[(table_name, col_name)]
        name_equals_value = all(member.name == member.value for member in enum_cls)
        assert not name_equals_value, f"{table_name}.{col_name} 名==值，不应在白名单中 (它本就无大小写问题)。"
