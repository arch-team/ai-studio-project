"""HyperPodCluster 仓库集成测试 - 真实数据库 CRUD 验证。

测试策略:
1. 使用真实数据库会话 (db_session fixture) 验证仓库行为，而非 mock。
2. 重点验证基类 PydanticRepository 提供的 get_by_id/create/update 对
   HyperPodCluster 实体真实可用 - 关键风险在 _to_entity/_to_model 转换、
   _updatable_fields 白名单、以及 Enum 字段 (status/health_status) 的持久化与读回。
3. 为下一任务 (集群读穿透服务) 提供前置保障。

文件命名: test_repo_hyperpod_cluster.py (repo = 仓库实现集成测试)

注意: 需要可连接的 MySQL (docker compose up -d mysql + alembic upgrade head)。
db_session fixture 在每个测试后回滚，故无需手动清理数据。每个测试仍使用唯一的
cluster_name/cluster_arn 前缀以防同一事务内的偶发冲突。
"""

import uuid
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.monitoring.domain.entities import HyperPodCluster
from src.modules.monitoring.domain.value_objects import ClusterStatus, HealthStatus
from src.modules.monitoring.infrastructure.repositories import HyperPodClusterRepositoryImpl


def _make_cluster(suffix: str) -> HyperPodCluster:
    """构造一个带唯一标识的 HyperPodCluster 实体 (含全部必填字段)。"""
    return HyperPodCluster(
        cluster_name=f"test-cluster-{suffix}",
        cluster_arn=f"arn:aws:sagemaker:us-east-1:123456789012:cluster/test-{suffix}",
        region="us-east-1",
        vpc_id="vpc-0abc123def456",
        instance_groups=[
            {"instance_group_name": "worker", "instance_type": "ml.g5.xlarge", "instance_count": 2},
        ],
        total_nodes=2,
        available_nodes=2,
        status=ClusterStatus.CREATING,
    )


class TestHyperPodClusterRepositoryCRUD:
    """验证基类 CRUD 方法对 HyperPodCluster 真实可用。"""

    async def test_create_and_get_by_arn(self, db_session: AsyncSession) -> None:
        """create 后能通过 get_by_arn 查回，且关键字段一致。"""
        repo = HyperPodClusterRepositoryImpl(db_session)
        suffix = uuid.uuid4().hex[:12]
        entity = _make_cluster(suffix)

        created = await repo.create(entity)

        # create 返回的实体应已分配主键
        assert created.id is not None

        fetched = await repo.get_by_arn(entity.cluster_arn)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.cluster_name == f"test-cluster-{suffix}"
        assert fetched.cluster_arn == entity.cluster_arn
        assert fetched.region == "us-east-1"
        assert fetched.vpc_id == "vpc-0abc123def456"
        assert fetched.total_nodes == 2
        assert fetched.available_nodes == 2
        # JSON 字段往返一致
        assert fetched.instance_groups == entity.instance_groups
        # Enum 字段持久化与读回 (应为 Enum 成员而非裸字符串)
        assert fetched.status == ClusterStatus.CREATING
        assert fetched.health_status is None

    async def test_create_and_get_by_id(self, db_session: AsyncSession) -> None:
        """create 后用返回的 id 通过 get_by_id 查回。"""
        repo = HyperPodClusterRepositoryImpl(db_session)
        suffix = uuid.uuid4().hex[:12]
        entity = _make_cluster(suffix)

        created = await repo.create(entity)
        assert created.id is not None

        fetched = await repo.get_by_id(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.cluster_name == f"test-cluster-{suffix}"
        assert fetched.status == ClusterStatus.CREATING

    async def test_update_changes_status(self, db_session: AsyncSession) -> None:
        """update 修改 Enum 字段 status 后能持久化并读回 (验证 _updatable_fields 生效)。"""
        repo = HyperPodClusterRepositoryImpl(db_session)
        suffix = uuid.uuid4().hex[:12]
        created = await repo.create(_make_cluster(suffix))
        assert created.status == ClusterStatus.CREATING

        # 通过领域方法做合法状态转换 creating -> active
        created.activate()
        created.update_health(HealthStatus.HEALTHY)
        updated = await repo.update(created)

        assert updated.status == ClusterStatus.ACTIVE
        assert updated.health_status == HealthStatus.HEALTHY

        # 重新查询确认变更已落库 (而非仅内存对象)
        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.status == ClusterStatus.ACTIVE
        assert fetched.health_status == HealthStatus.HEALTHY

    async def test_update_changes_last_sync_at(self, db_session: AsyncSession) -> None:
        """update 能修改 last_sync_at (读穿透服务依赖此字段可写)。"""
        repo = HyperPodClusterRepositoryImpl(db_session)
        suffix = uuid.uuid4().hex[:12]
        created = await repo.create(_make_cluster(suffix))
        assert created.last_sync_at is None

        # mark_synced 设置 last_sync_at = utc_now()
        created.mark_synced()
        assert created.last_sync_at is not None
        expected_sync_at = created.last_sync_at.replace(tzinfo=None)

        updated = await repo.update(created)
        assert updated.last_sync_at is not None

        # 重新查询确认 last_sync_at 已落库 (从 NULL 变为有值)
        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.last_sync_at is not None
        # 落库值应与 update 返回的值一致 (二者都经过 DB 往返)
        assert fetched.last_sync_at == updated.last_sync_at
        # 落库值应接近实体设置的时间。
        # MySQL DATETIME(0) 会对微秒四舍五入 (可能 +1s)，故用 1s 容差而非精确相等。
        assert abs(fetched.last_sync_at.replace(tzinfo=None) - expected_sync_at) <= timedelta(seconds=1)
