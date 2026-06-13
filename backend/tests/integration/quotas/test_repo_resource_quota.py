"""ResourceQuota 仓库集成测试 - 真实数据库 Enum 持久化往返验证。

覆盖 resource_quotas 表的 quota_type / status 两个 Enum 列。
DB 列定义为小写 .value，SQLAlchemy 默认按成员名读写，修复前读回抛 LookupError。

文件命名: test_repo_resource_quota.py (repo = 仓库实现集成测试)
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.quotas.domain.entities import ResourceQuota
from src.modules.quotas.domain.value_objects import QuotaStatus, QuotaType
from src.modules.quotas.infrastructure.repositories import ResourceQuotaRepository


def _make_quota(suffix: str, **overrides: object) -> ResourceQuota:
    """构造带唯一名称的 ResourceQuota 实体。"""
    data: dict[str, object] = {
        "name": f"enum-quota-{suffix}",
        "quota_type": QuotaType.TEAM,
        "status": QuotaStatus.ACTIVE,
        "max_cpu_cores": 64,
        "max_gpu_count": 8,
        "max_memory_gb": 256,
    }
    data.update(overrides)
    return ResourceQuota(**data)


class TestResourceQuotaRepositoryEnumPersistence:
    """验证 ResourceQuota 的 Enum 字段经真实 DB 往返后保持正确成员。"""

    async def test_create_and_read_back_preserves_enums(self, db_session: AsyncSession) -> None:
        """create 后 get_by_id 读回，quota_type/status 保持原值。"""
        repo = ResourceQuotaRepository(db_session)
        suffix = uuid.uuid4().hex[:12]
        created = await repo.create(_make_quota(suffix))
        assert created.id is not None

        fetched = await repo.get_by_id(created.id)

        assert fetched is not None
        assert fetched.quota_type == QuotaType.TEAM
        assert fetched.status == QuotaStatus.ACTIVE

    async def test_read_back_all_quota_type_and_status_members(self, db_session: AsyncSession) -> None:
        """每个 QuotaType / QuotaStatus 成员都能往返。"""
        repo = ResourceQuotaRepository(db_session)
        for qtype in QuotaType:
            for status in QuotaStatus:
                suffix = uuid.uuid4().hex[:12]
                created = await repo.create(_make_quota(suffix, quota_type=qtype, status=status))
                fetched = await repo.get_by_id(created.id)
                assert fetched is not None
                assert fetched.quota_type == qtype
                assert fetched.status == status

    async def test_update_status_persists(self, db_session: AsyncSession) -> None:
        """update 修改 status Enum 后能落库并读回。"""
        repo = ResourceQuotaRepository(db_session)
        suffix = uuid.uuid4().hex[:12]
        created = await repo.create(_make_quota(suffix, status=QuotaStatus.ACTIVE))

        created.status = QuotaStatus.SUSPENDED
        await repo.update(created)

        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.status == QuotaStatus.SUSPENDED
