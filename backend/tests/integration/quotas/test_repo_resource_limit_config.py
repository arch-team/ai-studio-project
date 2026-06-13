"""ResourceLimitConfig 仓库集成测试 - 真实数据库 Enum 持久化往返验证。

覆盖 resource_limit_configs 表的 role / priority_default 两个 Enum 列。
DB 列定义为小写 .value，SQLAlchemy 默认按成员名读写，修复前读回抛 LookupError。

文件命名: test_repo_resource_limit_config.py (repo = 仓库实现集成测试)
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.quotas.domain.entities import ResourceLimitConfig
from src.modules.quotas.domain.value_objects import LimitRole, PriorityDefault
from src.modules.quotas.infrastructure.repositories import ResourceLimitConfigRepository


def _make_config(suffix: str, **overrides: object) -> ResourceLimitConfig:
    """构造带唯一名称的 ResourceLimitConfig 实体 (project_id 用唯一值避免唯一约束冲突)。"""
    data: dict[str, object] = {
        "config_name": f"enum-limit-{suffix}",
        "role": LimitRole.ENGINEER,
        "project_id": uuid.uuid4().int % 1_000_000_000,
        "priority_default": PriorityDefault.MEDIUM,
    }
    data.update(overrides)
    return ResourceLimitConfig(**data)


class TestResourceLimitConfigRepositoryEnumPersistence:
    """验证 ResourceLimitConfig 的 Enum 字段经真实 DB 往返后保持正确成员。"""

    async def test_create_and_read_back_preserves_enums(self, db_session: AsyncSession) -> None:
        """create 后 get_by_id 读回，role/priority_default 保持原值。"""
        repo = ResourceLimitConfigRepository(db_session)
        suffix = uuid.uuid4().hex[:12]
        created = await repo.create(_make_config(suffix))
        assert created.id is not None

        fetched = await repo.get_by_id(created.id)

        assert fetched is not None
        assert fetched.role == LimitRole.ENGINEER
        assert fetched.priority_default == PriorityDefault.MEDIUM

    async def test_read_back_all_role_members(self, db_session: AsyncSession) -> None:
        """每个 LimitRole 成员都能往返 (覆盖多字符值 project_manager)。"""
        repo = ResourceLimitConfigRepository(db_session)
        for role in LimitRole:
            suffix = uuid.uuid4().hex[:12]
            created = await repo.create(_make_config(suffix, role=role))
            fetched = await repo.get_by_id(created.id)
            assert fetched is not None
            assert fetched.role == role

    async def test_filter_by_role_matches(self, db_session: AsyncSession) -> None:
        """get_by_role_and_project 按 Enum 字段过滤能命中 (验证 enum 绑定方向)。"""
        repo = ResourceLimitConfigRepository(db_session)
        suffix = uuid.uuid4().hex[:12]
        config = _make_config(suffix, role=LimitRole.ADMIN)
        created = await repo.create(config)

        fetched = await repo.get_by_role_and_project(LimitRole.ADMIN, config.project_id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.role == LimitRole.ADMIN

    async def test_read_back_all_priority_members(self, db_session: AsyncSession) -> None:
        """每个 PriorityDefault 成员都能往返。"""
        repo = ResourceLimitConfigRepository(db_session)
        for priority in PriorityDefault:
            suffix = uuid.uuid4().hex[:12]
            created = await repo.create(_make_config(suffix, priority_default=priority))
            fetched = await repo.get_by_id(created.id)
            assert fetched is not None
            assert fetched.priority_default == priority
