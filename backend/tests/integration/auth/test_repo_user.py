"""User 仓库集成测试 - 真实数据库 Enum 持久化往返验证。

测试策略:
1. 使用真实 MySQL (db_session fixture) 而非 mock，专门覆盖 Enum 字段
   (status/role/auth_type) 的持久化与读回 —— 这是单测 mock session 无法发现的盲区。
2. 根因: DB ENUM 列定义为小写 .value (如 'active')，而 SQLAlchemy Enum() 默认
   按成员名 (.name, 如 'ACTIVE') 读写。列未设 values_callable 时，读回小写值
   会抛 LookupError: 'active' is not among the defined enum values。
3. 覆盖三条路径: create→get_by_id 读回、enum 字段过滤查询 (list/count)、update 往返。

文件命名: test_repo_user.py (repo = 仓库实现集成测试)
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities import User
from src.modules.auth.domain.value_objects import AuthType, UserRole, UserStatus
from src.modules.auth.infrastructure.repositories import UserRepositoryImpl


def _make_user(suffix: str, **overrides: object) -> User:
    """构造带唯一标识的 User 实体 (含全部必填字段)。"""
    data: dict[str, object] = {
        "username": f"enum-user-{suffix}",
        "email": f"enum-user-{suffix}@example.com",
        "status": UserStatus.ACTIVE,
        "role": UserRole.ADMIN,
        "auth_type": AuthType.LOCAL,
    }
    data.update(overrides)
    return User(**data)


class TestUserRepositoryEnumPersistence:
    """验证 User 的 Enum 字段经真实 DB 往返后保持正确成员。"""

    async def test_create_and_read_back_preserves_enums(self, db_session: AsyncSession) -> None:
        """create 后 get_by_id 读回，status/role/auth_type 三个 Enum 字段保持原值。"""
        repo = UserRepositoryImpl(db_session)
        suffix = uuid.uuid4().hex[:12]
        entity = _make_user(suffix)

        created = await repo.create(entity)
        assert created.id is not None

        # 真实 DB 读回 —— 修复前此处抛 LookupError
        fetched = await repo.get_by_id(created.id)

        assert fetched is not None
        assert fetched.status == UserStatus.ACTIVE
        assert fetched.role == UserRole.ADMIN
        assert fetched.auth_type == AuthType.LOCAL

    async def test_read_back_all_role_members(self, db_session: AsyncSession) -> None:
        """每个 UserRole 成员都能往返 (覆盖多字符值如 project_manager)。"""
        repo = UserRepositoryImpl(db_session)
        for role in UserRole:
            suffix = uuid.uuid4().hex[:12]
            created = await repo.create(_make_user(suffix, role=role))
            fetched = await repo.get_by_id(created.id)
            assert fetched is not None
            assert fetched.role == role

    async def test_filter_by_enum_status_matches(self, db_session: AsyncSession) -> None:
        """按 Enum 字段过滤查询能命中 (验证 WHERE status = :status 的 enum 绑定方向)。"""
        repo = UserRepositoryImpl(db_session)
        suffix = uuid.uuid4().hex[:12]
        created = await repo.create(_make_user(suffix, status=UserStatus.SUSPENDED, role=UserRole.VIEWER))

        results = await repo.list_users(status=UserStatus.SUSPENDED, role=UserRole.VIEWER, limit=200)

        assert any(u.id == created.id for u in results)

    async def test_update_enum_field_persists(self, db_session: AsyncSession) -> None:
        """update 修改 Enum 字段后能落库并读回。"""
        repo = UserRepositoryImpl(db_session)
        suffix = uuid.uuid4().hex[:12]
        created = await repo.create(_make_user(suffix, status=UserStatus.ACTIVE))

        created.suspend()  # status -> SUSPENDED
        updated = await repo.update(created)
        assert updated.status == UserStatus.SUSPENDED

        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.status == UserStatus.SUSPENDED
