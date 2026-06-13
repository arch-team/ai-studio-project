"""ClusterSyncService Unit Tests - TDD Red-Green-Refactor (Task 2C.2b).

测试集群读穿透同步服务：DB 为主，缺失/过期时回源 SageMaker describe-cluster 写库。
仅 mock 边界依赖（仓库 + SageMaker 客户端），不 mock 被测服务。
"""

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.modules.monitoring.application.services.cluster_sync_service import ClusterSyncService
from src.modules.monitoring.domain.entities import HyperPodCluster
from src.modules.monitoring.domain.value_objects import ClusterStatus
from src.shared.utils import utc_now

_CLUSTER_NAME = "ai-platform-dev-hyperpod"
_CLUSTER_ARN = "arn:aws:sagemaker:us-east-1:897473508751:cluster/abc"


def _fresh_cluster() -> HyperPodCluster:
    """构造一个刚刚同步过的集群实体（last_sync_at=现在）。"""
    return HyperPodCluster(
        id=1,
        cluster_name=_CLUSTER_NAME,
        cluster_arn=_CLUSTER_ARN,
        region="us-east-1",
        vpc_id="vpc-12345678",
        instance_groups=[{"InstanceGroupName": "g", "InstanceType": "ml.g5.2xlarge", "CurrentCount": 1}],
        total_nodes=1,
        available_nodes=1,
        status=ClusterStatus.ACTIVE,
        last_sync_at=utc_now(),
    )


def _stale_cluster() -> HyperPodCluster:
    """构造一个已过期的集群实体（last_sync_at=10 分钟前，超 TTL）。"""
    return HyperPodCluster(
        id=1,
        cluster_name=_CLUSTER_NAME,
        cluster_arn=_CLUSTER_ARN,
        region="us-east-1",
        vpc_id="vpc-12345678",
        instance_groups=[{"InstanceGroupName": "g", "InstanceType": "ml.g5.2xlarge", "CurrentCount": 1}],
        total_nodes=1,
        available_nodes=1,
        status=ClusterStatus.ACTIVE,
        last_sync_at=utc_now() - timedelta(minutes=10),
    )


def _fake_describe_cluster() -> dict[str, Any]:
    """模拟 SageMaker describe-cluster 真实响应（InService 集群）。"""
    return {
        "ClusterName": _CLUSTER_NAME,
        "ClusterArn": _CLUSTER_ARN,
        "ClusterStatus": "InService",
        "InstanceGroups": [
            {
                "InstanceGroupName": "g",
                "InstanceType": "ml.g5.2xlarge",
                "CurrentCount": 2,
                "TargetCount": 2,
                "ThreadsPerCore": 1,
            },
            {
                "InstanceGroupName": "cpu",
                "InstanceType": "ml.m5.2xlarge",
                "CurrentCount": 1,
                "TargetCount": 1,
            },
        ],
        "VpcConfig": {
            "SecurityGroupIds": ["sg-123"],
            "Subnets": ["subnet-abc"],
        },
    }


@pytest.fixture
def repo() -> AsyncMock:
    """Mock IHyperPodClusterRepository。"""
    mock = AsyncMock()
    mock.list_clusters = AsyncMock(return_value=[])
    mock.get_by_arn = AsyncMock(return_value=None)
    mock.create = AsyncMock(side_effect=lambda entity: entity)
    mock.update = AsyncMock(side_effect=lambda entity: entity)
    return mock


@pytest.fixture
def sagemaker() -> AsyncMock:
    """Mock SageMakerClusterClient。"""
    mock = AsyncMock()
    mock.describe_cluster = AsyncMock(return_value=_fake_describe_cluster())
    return mock


# === 读穿透行为 ===


async def test_get_clusters_refetches_when_db_empty(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    # 缓存未命中（外层 + 锁内双重检查均空）→ 回源写库 → 再次 list 返回新记录
    repo.list_clusters.side_effect = [[], [], [_fresh_cluster()]]
    repo.get_by_arn.return_value = None

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)
    result = await svc.get_clusters()

    sagemaker.describe_cluster.assert_awaited()
    repo.create.assert_awaited()
    assert len(result) >= 1


async def test_get_clusters_uses_db_when_fresh(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    repo.list_clusters.return_value = [_fresh_cluster()]

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300)
    result = await svc.get_clusters()

    sagemaker.describe_cluster.assert_not_awaited()
    assert len(result) == 1


async def test_get_clusters_updates_existing_when_stale(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    stale = _stale_cluster()
    repo.list_clusters.return_value = [stale]
    repo.get_by_arn.return_value = stale

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)
    await svc.get_clusters()

    sagemaker.describe_cluster.assert_awaited()
    repo.update.assert_awaited()
    repo.create.assert_not_awaited()


async def test_get_clusters_creates_when_arn_not_in_db(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    # DB 为空触发回源，但回源后 ARN 在库中查不到 → 走 create
    repo.list_clusters.return_value = []
    repo.get_by_arn.return_value = None

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)
    await svc.get_clusters()

    repo.create.assert_awaited()
    repo.update.assert_not_awaited()


# === 状态与字段映射 ===


async def test_status_mapping_inservice_to_active(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    repo.list_clusters.return_value = []
    repo.get_by_arn.return_value = None

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)
    await svc.get_clusters()

    created_entity = repo.create.call_args.args[0]
    assert created_entity.status == ClusterStatus.ACTIVE


@pytest.mark.parametrize(
    "sagemaker_status,expected",
    [
        ("InService", ClusterStatus.ACTIVE),
        ("Creating", ClusterStatus.CREATING),
        ("Updating", ClusterStatus.UPDATING),
        ("Deleting", ClusterStatus.DELETING),
        ("Failed", ClusterStatus.FAILED),
        ("RollingBack", ClusterStatus.UPDATING),
        ("SystemUpdating", ClusterStatus.UPDATING),
        ("SomethingUnknown", ClusterStatus.CREATING),  # 未知值兜底
    ],
)
async def test_status_mapping_all_variants(
    repo: AsyncMock,
    sagemaker: AsyncMock,
    sagemaker_status: str,
    expected: ClusterStatus,
) -> None:
    raw = _fake_describe_cluster()
    raw["ClusterStatus"] = sagemaker_status
    sagemaker.describe_cluster.return_value = raw
    repo.list_clusters.return_value = []
    repo.get_by_arn.return_value = None

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)
    await svc.get_clusters()

    created_entity = repo.create.call_args.args[0]
    assert created_entity.status == expected


async def test_map_to_entity_field_mapping(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    repo.list_clusters.return_value = []
    repo.get_by_arn.return_value = None

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)
    await svc.get_clusters()

    entity = repo.create.call_args.args[0]
    assert entity.cluster_name == _CLUSTER_NAME
    assert entity.cluster_arn == _CLUSTER_ARN
    # total_nodes = sum(CurrentCount) = 2 + 1
    assert entity.total_nodes == 3
    # total_gpu_count 仅累计 GPU 实例组（ml.g5）的 CurrentCount = 2
    assert entity.total_gpu_count == 2
    # instance_groups 原样保留 list[dict]
    assert isinstance(entity.instance_groups, list)
    assert len(entity.instance_groups) == 2
    # last_sync_at 被设置（新鲜）
    assert entity.last_sync_at is not None


async def test_map_to_entity_handles_null_current_count(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    # 健壮性回归：SageMaker 返回 CurrentCount=null（key 在但值为 None）时，
    # int(None) 会抛 TypeError 导致写库阶段崩溃。加固后应兜底为 0，写库不抛。
    raw = _fake_describe_cluster()
    raw["InstanceGroups"] = [
        {"InstanceGroupName": "g", "InstanceType": "ml.g5.2xlarge", "CurrentCount": None},
        {"InstanceGroupName": "cpu", "InstanceType": "ml.m5.2xlarge", "CurrentCount": 1},
    ]
    sagemaker.describe_cluster.return_value = raw
    repo.list_clusters.return_value = []
    repo.get_by_arn.return_value = None

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)
    # 不抛 TypeError 即说明加固生效
    await svc.get_clusters()

    entity = repo.create.call_args.args[0]
    # None 兜底为 0：total_nodes = 0 + 1
    assert entity.total_nodes == 1
    # GPU 组 CurrentCount=None 兜底为 0 → 无 GPU 计入 → total_gpu_count 记 None
    assert entity.total_gpu_count is None


async def test_map_to_entity_vpc_id_fallback_when_missing(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    # VpcConfig 不提供 vpc_id，必填字段必须安全兜底，不能让实体构造失败
    raw = _fake_describe_cluster()
    raw.pop("VpcConfig", None)
    sagemaker.describe_cluster.return_value = raw
    repo.list_clusters.return_value = []
    repo.get_by_arn.return_value = None

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)
    await svc.get_clusters()

    entity = repo.create.call_args.args[0]
    assert entity.vpc_id  # 非空（占位值或推导值）


# === 单飞锁双重检查 ===


async def test_concurrent_get_clusters_single_flight(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    # 首次 DB 空，回源后第二次 list 返回新鲜数据；并发调用应只回源一次
    import asyncio

    fresh = _fresh_cluster()
    repo.list_clusters.side_effect = [[], [], [fresh], [fresh]]
    repo.get_by_arn.return_value = None

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)
    await asyncio.gather(svc.get_clusters(), svc.get_clusters())

    # 单飞锁保证 describe_cluster 只被调用一次
    assert sagemaker.describe_cluster.await_count == 1


# === 异常透传契约 ===


async def test_get_clusters_propagates_describe_cluster_error(repo: AsyncMock, sagemaker: AsyncMock) -> None:
    # DB 空触发回源，describe_cluster 失败（如 AMP/SageMaker 不可达）时异常须向上抛出，
    # 由 API 层（2C.4）降级处理，服务层不吞异常；隐含验证单飞锁正常释放（不死锁）。
    repo.list_clusters.return_value = []
    sagemaker.describe_cluster.side_effect = Exception("AMP down")

    svc = ClusterSyncService(repo, sagemaker, ttl_seconds=300, cluster_name=_CLUSTER_NAME)

    with pytest.raises(Exception, match="AMP down"):
        await svc.get_clusters()

    # 锁已释放：再次调用仍能进入回源逻辑（若死锁此处会超时挂起）
    with pytest.raises(Exception, match="AMP down"):
        await svc.get_clusters()
