"""AuditLog 仓库集成测试 - 真实数据库 Enum 持久化往返验证。

覆盖 audit_logs 表的 operation_type / resource_type / status 三个 Enum 列。
audit 模块的特殊性:
- DB 列经迁移 h8i9j0k1l2m3 已改为小写 .value (如 'create')。
- Domain VO (OperationType 等) 的 .value 是小写，与 DB 对齐。
- 修复前 ORM 层定义了独立的大写本地 enum，且 repository 查询方法用
  ModelXxx(domain.value) 构造，会因大小写不匹配抛 ValueError/LookupError。

文件命名: test_repo_audit_log.py (repo = 仓库实现集成测试)
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit.domain.entities import AuditLog
from src.modules.audit.domain.value_objects import AuditStatus, OperationType, ResourceType
from src.modules.audit.infrastructure.repositories import AuditLogRepositoryImpl
from src.modules.auth.domain.entities import User
from src.modules.auth.domain.value_objects import AuthType, UserRole, UserStatus
from src.modules.auth.infrastructure.repositories import UserRepositoryImpl


@pytest.fixture
async def audit_user_id(db_session: AsyncSession) -> int:
    """创建一个真实 user 并返回其 id (audit_logs.user_id 有外键约束)。"""
    suffix = uuid.uuid4().hex[:12]
    user = User(
        username=f"audit-actor-{suffix}",
        email=f"audit-actor-{suffix}@example.com",
        status=UserStatus.ACTIVE,
        role=UserRole.ENGINEER,
        auth_type=AuthType.LOCAL,
    )
    created = await UserRepositoryImpl(db_session).create(user)
    assert created.id is not None
    return created.id


def _make_log(user_id: int, **overrides: object) -> AuditLog:
    """构造一条 AuditLog 实体。"""
    data: dict[str, object] = {
        "operation_type": OperationType.CREATE,
        "resource_type": ResourceType.TRAINING_JOB,
        "status": AuditStatus.SUCCESS,
        "user_id": user_id,
        "resource_id": f"res-{uuid.uuid4().hex[:8]}",
    }
    data.update(overrides)
    return AuditLog(**data)


class TestAuditLogRepositoryEnumPersistence:
    """验证 AuditLog 的 Enum 字段经真实 DB 往返后保持正确成员。"""

    async def test_create_and_read_back_preserves_enums(self, db_session: AsyncSession, audit_user_id: int) -> None:
        """create→get_by_id 读回，operation_type/resource_type/status 保持原值。"""
        repo = AuditLogRepositoryImpl(db_session)
        created = await repo.create(_make_log(audit_user_id))
        assert created.id is not None

        fetched = await repo.get_by_id(created.id)

        assert fetched is not None
        assert fetched.operation_type == OperationType.CREATE
        assert fetched.resource_type == ResourceType.TRAINING_JOB
        assert fetched.status == AuditStatus.SUCCESS

    async def test_read_back_all_operation_types(self, db_session: AsyncSession, audit_user_id: int) -> None:
        """每个 OperationType 成员都能往返。"""
        repo = AuditLogRepositoryImpl(db_session)
        for op in OperationType:
            created = await repo.create(_make_log(audit_user_id, operation_type=op))
            fetched = await repo.get_by_id(created.id)
            assert fetched is not None
            assert fetched.operation_type == op

    async def test_read_back_all_resource_types(self, db_session: AsyncSession, audit_user_id: int) -> None:
        """每个 ResourceType 成员都能往返 (覆盖多字符值 training_job)。"""
        repo = AuditLogRepositoryImpl(db_session)
        for rtype in ResourceType:
            created = await repo.create(_make_log(audit_user_id, resource_type=rtype))
            fetched = await repo.get_by_id(created.id)
            assert fetched is not None
            assert fetched.resource_type == rtype

    async def test_get_by_resource_filters_by_enum(self, db_session: AsyncSession, audit_user_id: int) -> None:
        """get_by_resource 按 Enum 字段过滤能命中 (修复前 ModelResourceType(value) 抛 ValueError)。"""
        repo = AuditLogRepositoryImpl(db_session)
        log = _make_log(audit_user_id, resource_type=ResourceType.MODEL)
        created = await repo.create(log)

        results = await repo.get_by_resource(ResourceType.MODEL, log.resource_id)

        assert any(r.id == created.id for r in results)

    async def test_get_by_operation_type_filters_by_enum(self, db_session: AsyncSession, audit_user_id: int) -> None:
        """get_by_operation_type 按 Enum 字段过滤能命中 (修复前 ModelOperationType(value) 抛 ValueError)。"""
        repo = AuditLogRepositoryImpl(db_session)
        created = await repo.create(_make_log(audit_user_id, operation_type=OperationType.DELETE))

        results = await repo.get_by_operation_type(OperationType.DELETE)

        assert any(r.id == created.id for r in results)
