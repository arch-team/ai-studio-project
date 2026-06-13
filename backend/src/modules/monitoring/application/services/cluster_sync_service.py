"""集群读穿透同步服务 (Task 2C.2b).

监控页"集群概览"的数据来源：DB 为主，记录缺失或超 TTL 时回源
SageMaker describe-cluster，映射写库后返回。

数据策略：读穿透缓存（read-through cache）
- `hyperpod_clusters` 表为权威缓存
- 命中且未过期 → 直接返回 DB 记录
- 缺失或过期 → 单飞锁内回源 SageMaker，覆盖式刷新写库

注意：从 SageMaker 同步是"覆盖式"刷新而非业务状态流转，
因此构造/更新实体时直接设 status，不走 transition_to 状态机。
"""

import asyncio
from typing import Any

import structlog

from src.shared.infrastructure import get_settings
from src.shared.utils import utc_now

from ...domain.entities import HyperPodCluster
from ...domain.repositories import IHyperPodClusterRepository
from ...domain.value_objects import ClusterStatus
from ..interfaces import ISageMakerClusterClient

logger = structlog.get_logger(__name__)

# SageMaker ClusterStatus → 领域 ClusterStatus 映射。
# SageMaker 的状态值（InService/Creating/...）与领域 enum（active/creating/...）不一致，必须映射。
_SAGEMAKER_STATUS_MAP: dict[str, ClusterStatus] = {
    "InService": ClusterStatus.ACTIVE,
    "Creating": ClusterStatus.CREATING,
    "Updating": ClusterStatus.UPDATING,
    "Deleting": ClusterStatus.DELETING,
    "Failed": ClusterStatus.FAILED,
    "RollingBack": ClusterStatus.UPDATING,
    "SystemUpdating": ClusterStatus.UPDATING,
}

# 未知 SageMaker 状态的兜底领域状态
_DEFAULT_STATUS = ClusterStatus.CREATING

# GPU 实例类型前缀（用于粗略累计 GPU 数）。
# 仅覆盖 ml.g/ml.p 系列，trn/inf 等加速器不计入。
_GPU_INSTANCE_PREFIXES = ("ml.g", "ml.p")


class ClusterSyncService:
    """集群读穿透同步服务.

    DB 为主缓存，缺失/过期时回源 SageMaker describe-cluster 写库再返回。
    使用单飞锁（asyncio.Lock）+ 双重检查避免并发回源风暴。

    当前按单集群部署：回源仅刷新 settings 配置的集群（hyperpod_cluster_name）。
    """

    def __init__(
        self,
        cluster_repo: IHyperPodClusterRepository,
        sagemaker_client: ISageMakerClusterClient,
        ttl_seconds: int = 300,
        cluster_name: str | None = None,
    ):
        self._repo = cluster_repo
        self._sagemaker = sagemaker_client
        self._ttl_seconds = ttl_seconds
        self._cluster_name = cluster_name or get_settings().hyperpod_cluster_name
        self._lock = asyncio.Lock()

    async def get_clusters(self) -> list[HyperPodCluster]:
        """获取集群列表（读穿透）.

        DB 命中且新鲜 → 直接返回；否则单飞锁内回源刷新后返回。
        """
        existing = await self._repo.list_clusters()
        if existing and self._is_fresh(existing):
            return existing

        async with self._lock:
            # 双重检查：等锁期间可能已有其他协程完成回源
            existing = await self._repo.list_clusters()
            if existing and self._is_fresh(existing):
                return existing

            await self._sync_from_sagemaker()
            return await self._repo.list_clusters()

    def _is_fresh(self, clusters: list[HyperPodCluster]) -> bool:
        """所有集群均已同步且未超 TTL 视为新鲜."""
        now = utc_now()
        for cluster in clusters:
            if cluster.last_sync_at is None:
                return False
            if (now - cluster.last_sync_at).total_seconds() >= self._ttl_seconds:
                return False
        return True

    async def _sync_from_sagemaker(self) -> None:
        """回源 SageMaker 并覆盖式写库.

        按 cluster_arn 查重：存在则 update，否则 create。
        """
        if not self._cluster_name:
            logger.warning("cluster_sync_skipped_no_cluster_name")
            return

        # describe_cluster 异常有意透传，由 API 层（2C.4）降级处理，此处不捕获。
        raw = await self._sagemaker.describe_cluster(self._cluster_name)
        entity = self._map_to_entity(raw)

        existing = await self._repo.get_by_arn(entity.cluster_arn)
        if existing is not None:
            entity.id = existing.id
            await self._repo.update(entity)
            logger.info("cluster_synced_update", cluster_name=entity.cluster_name, cluster_arn=entity.cluster_arn)
        else:
            await self._repo.create(entity)
            logger.info("cluster_synced_create", cluster_name=entity.cluster_name, cluster_arn=entity.cluster_arn)

    def _map_to_entity(self, raw: dict[str, Any]) -> HyperPodCluster:
        """将 SageMaker describe-cluster 响应映射为领域实体.

        覆盖式刷新：直接传 status（经映射），不走 transition_to 状态机。
        """
        instance_groups: list[dict[str, Any]] = raw.get("InstanceGroups", [])
        total_nodes = sum(int(g.get("CurrentCount", 0)) for g in instance_groups)
        gpu_count = sum(
            int(g.get("CurrentCount", 0))
            for g in instance_groups
            if str(g.get("InstanceType", "")).startswith(_GPU_INSTANCE_PREFIXES)
        )

        return HyperPodCluster(
            cluster_name=raw.get("ClusterName", self._cluster_name or "unknown"),
            cluster_arn=raw.get("ClusterArn", ""),
            region=get_settings().aws_region,
            vpc_id=self._extract_vpc_id(raw),
            instance_groups=instance_groups,
            total_nodes=total_nodes,
            available_nodes=total_nodes,
            # 仅覆盖 ml.g/ml.p 系列，trn/inf 等加速器不计入；无 GPU 实例组时记 None。
            total_gpu_count=gpu_count or None,
            status=self._map_status(raw.get("ClusterStatus", "")),
            last_sync_at=utc_now(),
        )

    @staticmethod
    def _map_status(sagemaker_status: str) -> ClusterStatus:
        """SageMaker 状态 → 领域状态，未知值兜底为 CREATING."""
        mapped = _SAGEMAKER_STATUS_MAP.get(sagemaker_status)
        if mapped is None:
            logger.warning("cluster_status_unmapped", sagemaker_status=sagemaker_status)
            return _DEFAULT_STATUS
        return mapped

    def _extract_vpc_id(self, raw: dict[str, Any]) -> str:
        """提取 vpc_id（必填字段安全兜底）.

        describe-cluster 的 VpcConfig 仅含 SecurityGroupIds/Subnets，不直接给 vpc_id。
        务实处理：取响应中的显式 vpc_id（若有），否则兜底 "unknown"，
        避免必填字段缺失导致实体构造失败。
        Settings 暂无 vpc_id 配置，无法从响应取到时用 unknown 占位。
        """
        vpc_config = raw.get("VpcConfig") or {}
        vpc_id = vpc_config.get("VpcId")
        if vpc_id:
            return str(vpc_id)

        return "unknown"
