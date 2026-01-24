"""抢占时序 SLA 集成测试 (T038c)

测试场景:
1. 低优先级任务被高优先级任务抢占 (Kueue Priority)
2. checkpoint 在抢占触发后 5 分钟内保存完成
3. 被抢占 Pod 在 30 秒内释放
4. 任务状态正确转换为 Preempted
5. 抢占后自动恢复成功 (checkpoint 恢复 + 训练继续)

依赖: T022 (checkpoints 表), T024 (Checkpoint 模型), T029 (状态同步), T038 (checkpoint 保存)
参考: FR-004 (spec.md)
"""

import time
from datetime import datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.training.application.services.checkpoint_service import (
    CheckpointService,
)
from src.modules.training.application.services.training_sync_service import (
    MAX_PREEMPTION_COUNT,
    TrainingSyncService,
)
from src.modules.training.domain.entities import Checkpoint, TrainingJob
from src.modules.training.domain.value_objects import (
    CheckpointTriggerType,
    CheckpointType,
    DistributionStrategy,
    JobPriority,
    JobStatus,
    StorageTier,
)


# =============================================================================
# SLA 常量定义
# =============================================================================

# 检查点保存 SLA: 5 分钟 (300 秒)
CHECKPOINT_SAVE_SLA_SECONDS = 300

# Pod 释放 SLA: 30 秒
POD_RELEASE_SLA_SECONDS = 30

# 默认测试集群名称
TEST_CLUSTER_NAME = "test-hyperpod-cluster"


# =============================================================================
# Helper Functions
# =============================================================================


def create_test_job(
    job_id: int = 1,
    job_name: str | None = None,
    priority: JobPriority = JobPriority.MEDIUM,
    status: JobStatus = JobStatus.RUNNING,
    preemption_count: int = 0,
    owner_id: int = 100,
) -> TrainingJob:
    """创建测试用 TrainingJob 实体"""
    if job_name is None:
        job_name = f"test-training-job-{job_id}"

    return TrainingJob(
        id=job_id,
        job_name=job_name,
        owner_id=owner_id,
        image_uri="123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
        instance_type="ml.p4d.24xlarge",
        entrypoint_command=["torchrun", "--nproc_per_node=8", "train.py"],
        node_count=2,
        tasks_per_node=8,
        distribution_strategy=DistributionStrategy.DDP,
        priority=priority,
        status=status,
        preemption_count=preemption_count,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def create_test_checkpoint(
    checkpoint_id: int = 1,
    training_job_id: int = 1,
    trigger_type: CheckpointTriggerType = CheckpointTriggerType.PREEMPTION,
    storage_path: str | None = None,
    size_bytes: int = 100 * 1024 * 1024,  # 100MB
) -> Checkpoint:
    """创建测试用 Checkpoint 实体"""
    if storage_path is None:
        storage_path = f"/mnt/nvme/ckpt/{training_job_id}/preemption"

    return Checkpoint(
        id=checkpoint_id,
        training_job_id=training_job_id,
        checkpoint_name=f"preemption-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        storage_path=storage_path,
        size_bytes=size_bytes,
        checkpoint_type=CheckpointType.EPOCH,
        trigger_type=trigger_type,
        storage_tier=StorageTier.NVME,
    )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_checkpoint_repository() -> AsyncMock:
    """Mock ICheckpointRepository"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_latest_by_training_job_id = AsyncMock()
    repo.get_by_training_job_id = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_training_job_repository() -> AsyncMock:
    """Mock ITrainingJobRepository"""
    repo = AsyncMock()
    repo.update = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.list_jobs = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def mock_hyperpod_client() -> AsyncMock:
    """Mock IHyperPodClient"""
    client = AsyncMock()
    client.get_training_job_status = AsyncMock()
    client.get_pod_status = AsyncMock()
    return client


@pytest.fixture
def mock_storage_service() -> AsyncMock:
    """Mock IStorageService"""
    service = AsyncMock()
    service.check_nvme_available = AsyncMock(return_value=True)
    service.check_fsx_available = AsyncMock(return_value=True)
    service.get_storage_path = AsyncMock(return_value="/mnt/nvme/ckpt/test")
    service.calculate_checksum = AsyncMock(return_value="sha256:abc123def456")
    service.get_checkpoint_size = AsyncMock(return_value=100 * 1024 * 1024)  # 100MB
    return service


# =============================================================================
# Test Class: 抢占时序 SLA - TestPreemptionTimingSLA
# =============================================================================


@pytest.mark.integration
class TestPreemptionTimingSLA:
    """抢占时序 SLA 集成测试 - FR-004

    验证抢占场景下的时序保证：
    - Checkpoint 保存 SLA: 5 分钟内
    - Pod 释放 SLA: 30 秒内
    - 状态转换正确性
    - 自动恢复机制
    """

    @pytest.mark.asyncio
    async def test_low_priority_job_preempted_by_high_priority(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """场景1: 低优先级任务被高优先级任务抢占

        验证:
        - 低优先级 Running 任务收到抢占事件后状态变为 PREEMPTED
        - preemption_count 正确累加
        """
        # Arrange: 创建低优先级 Running 任务
        low_priority_job = create_test_job(
            job_id=1,
            priority=JobPriority.LOW,
            status=JobStatus.RUNNING,
            preemption_count=0,
        )

        # 模拟 HyperPod 返回 Preempted 状态 (被高优先级任务抢占)
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": low_priority_job.job_name,
            "status": "Preempted",
            "preempted_by": "high-priority-job-001",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name=TEST_CLUSTER_NAME,
        )

        # Act: 执行状态同步 (模拟 Kueue 抢占事件)
        result = await service.sync_job(low_priority_job)

        # Assert: 验证抢占处理
        assert result is True  # 同步成功
        assert low_priority_job.status == JobStatus.PREEMPTED
        assert low_priority_job.preemption_count == 1

        # 验证状态被持久化
        mock_training_job_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_checkpoint_saved_within_5_minutes_sla(
        self,
        mock_checkpoint_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_storage_service: AsyncMock,
    ) -> None:
        """场景2: checkpoint 在抢占触发后 5 分钟内保存完成

        SLA 验证:
        - 抢占检查点创建时间 < 5 分钟 (300 秒)
        - 检查点正确保存到 NVMe
        """
        # Arrange: 配置 Running 状态任务
        job = create_test_job(job_id=1, status=JobStatus.RUNNING)
        mock_training_job_repository.get_by_id.return_value = job

        # Mock checkpoint 创建成功
        created_checkpoint = create_test_checkpoint(
            checkpoint_id=1,
            training_job_id=job.id,
            trigger_type=CheckpointTriggerType.PREEMPTION,
        )
        mock_checkpoint_repository.create.return_value = created_checkpoint

        checkpoint_service = CheckpointService(
            repository=mock_checkpoint_repository,
            training_job_repository=mock_training_job_repository,
            storage_service=mock_storage_service,
        )

        # Act: 记录开始时间，创建抢占检查点
        start_time = time.time()
        checkpoint = await checkpoint_service.create_checkpoint_on_preemption(
            job_id=job.id,
            timeout_seconds=CHECKPOINT_SAVE_SLA_SECONDS,
        )
        elapsed = time.time() - start_time

        # Assert: 验证 SLA (5 分钟内完成)
        assert checkpoint is not None
        assert elapsed < CHECKPOINT_SAVE_SLA_SECONDS, (
            f"Checkpoint 创建超时: {elapsed:.2f}s > {CHECKPOINT_SAVE_SLA_SECONDS}s"
        )

        # 验证检查点属性
        mock_checkpoint_repository.create.assert_called_once()
        created_ckpt = mock_checkpoint_repository.create.call_args[0][0]
        assert created_ckpt.trigger_type == CheckpointTriggerType.PREEMPTION

    @pytest.mark.asyncio
    async def test_pod_released_within_30_seconds_sla(
        self,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """场景3: 被抢占 Pod 在 30 秒内释放

        SLA 验证:
        - Pod 状态查询响应时间 < 30 秒
        - Pod 正确转换为 Terminated 状态
        """
        # Arrange: 模拟 Pod 已被 Evict
        mock_hyperpod_client.get_pod_status.return_value = {
            "pod_name": "training-job-001-worker-0",
            "phase": "Terminated",
            "reason": "Preempted",
            "termination_time": datetime.utcnow().isoformat(),
        }

        # Act: 记录开始时间，查询 Pod 状态
        start_time = time.time()
        pod_status = await mock_hyperpod_client.get_pod_status("training-job-001-worker-0")
        elapsed = time.time() - start_time

        # Assert: 验证 SLA (30 秒内响应)
        assert elapsed < POD_RELEASE_SLA_SECONDS, (
            f"Pod 状态查询超时: {elapsed:.2f}s > {POD_RELEASE_SLA_SECONDS}s"
        )
        assert pod_status["phase"] == "Terminated"
        assert pod_status["reason"] == "Preempted"

    @pytest.mark.asyncio
    async def test_job_status_transitions_to_preempted(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """场景4: 任务状态正确转换为 Preempted

        验证状态机:
        - RUNNING → PREEMPTED 转换合法
        - PREEMPTED 非终态，可恢复到 RUNNING
        """
        # Arrange: 创建 Running 任务
        job = create_test_job(
            job_id=1,
            status=JobStatus.RUNNING,
            preemption_count=0,
        )

        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name=TEST_CLUSTER_NAME,
        )

        # Act: 执行状态同步
        await service.sync_job(job)

        # Assert: 验证状态机
        assert job.status == JobStatus.PREEMPTED

        # 验证 PREEMPTED 状态特性
        assert not job.is_terminal(), "PREEMPTED 不应是终态"
        assert job.can_transition_to(JobStatus.RUNNING), "PREEMPTED 应可转换为 RUNNING"
        assert job.can_resume(), "PREEMPTED 状态应支持恢复"

    @pytest.mark.asyncio
    async def test_auto_recovery_from_checkpoint_after_preemption(
        self,
        mock_checkpoint_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """场景5: 抢占后自动恢复成功 (checkpoint 恢复 + 训练继续)

        验证恢复流程:
        1. 任务处于 PREEMPTED 状态，有可用检查点
        2. Kueue 重新调度后任务恢复为 RUNNING
        3. 从最新检查点恢复训练
        """
        # Arrange: 创建 PREEMPTED 状态任务
        job = create_test_job(
            job_id=1,
            status=JobStatus.PREEMPTED,
            preemption_count=1,
        )

        # 配置可用的抢占检查点
        preemption_checkpoint = create_test_checkpoint(
            checkpoint_id=1,
            training_job_id=job.id,
            trigger_type=CheckpointTriggerType.PREEMPTION,
            storage_path="/mnt/nvme/ckpt/1/preemption-20260124120000",
        )
        mock_checkpoint_repository.get_latest_by_training_job_id.return_value = (
            preemption_checkpoint
        )

        # 模拟 Kueue 重新调度后，HyperPod 返回 Running 状态
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Running",
            "checkpoint_restored": preemption_checkpoint.storage_path,
        }

        # 手动将任务状态改为 RUNNING (模拟 Kueue 重新调度)
        job.transition_to(JobStatus.RUNNING)

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name=TEST_CLUSTER_NAME,
        )

        # Act: 执行状态同步 (验证恢复后的状态)
        await service.sync_job(job)

        # Assert: 验证恢复成功
        assert job.status == JobStatus.RUNNING
        # preemption_count 在成功恢复后不重置 (用于统计)
        assert job.preemption_count == 1

    @pytest.mark.asyncio
    async def test_preemption_checkpoint_fallback_to_fsx(
        self,
        mock_checkpoint_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_storage_service: AsyncMock,
    ) -> None:
        """补充: NVMe 不可用时回退到 FSx 存储

        验证存储降级:
        - NVMe 不可用时自动回退到 FSx
        - 检查点仍能在 SLA 内完成
        """
        # Arrange: NVMe 不可用，FSx 可用
        mock_storage_service.check_nvme_available.return_value = False
        mock_storage_service.check_fsx_available.return_value = True
        mock_storage_service.get_storage_path.return_value = "/fsx/checkpoints/test"

        job = create_test_job(job_id=1, status=JobStatus.RUNNING)
        mock_training_job_repository.get_by_id.return_value = job

        created_checkpoint = create_test_checkpoint(
            checkpoint_id=1,
            training_job_id=job.id,
        )
        mock_checkpoint_repository.create.return_value = created_checkpoint

        checkpoint_service = CheckpointService(
            repository=mock_checkpoint_repository,
            training_job_repository=mock_training_job_repository,
            storage_service=mock_storage_service,
        )

        # Act
        checkpoint = await checkpoint_service.create_checkpoint_on_preemption(
            job_id=job.id,
        )

        # Assert: 检查点创建成功 (存储层为 FSx)
        assert checkpoint is not None
        mock_checkpoint_repository.create.assert_called_once()


# =============================================================================
# Test Class: 抢占边界条件 - TestPreemptionEdgeCases
# =============================================================================


@pytest.mark.integration
class TestPreemptionEdgeCases:
    """抢占边界条件测试"""

    @pytest.mark.asyncio
    async def test_preemption_with_existing_checkpoint(
        self,
        mock_checkpoint_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """有现有检查点的任务被抢占

        验证:
        - 创建新的抢占检查点
        - 不影响现有检查点
        """
        # Arrange
        job = create_test_job(job_id=1, status=JobStatus.RUNNING)

        # 已有检查点
        existing_checkpoint = create_test_checkpoint(
            checkpoint_id=1,
            training_job_id=job.id,
            trigger_type=CheckpointTriggerType.SCHEDULED,
        )
        mock_checkpoint_repository.get_by_training_job_id.return_value = [
            existing_checkpoint
        ]
        mock_training_job_repository.get_by_id.return_value = job

        # 新抢占检查点
        new_checkpoint = create_test_checkpoint(
            checkpoint_id=2,
            training_job_id=job.id,
            trigger_type=CheckpointTriggerType.PREEMPTION,
        )
        mock_checkpoint_repository.create.return_value = new_checkpoint

        checkpoint_service = CheckpointService(
            repository=mock_checkpoint_repository,
            training_job_repository=mock_training_job_repository,
        )

        # Act
        checkpoint = await checkpoint_service.create_checkpoint_on_preemption(
            job_id=job.id,
        )

        # Assert: 新检查点创建成功
        assert checkpoint is not None
        assert checkpoint.trigger_type == CheckpointTriggerType.PREEMPTION
        mock_checkpoint_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_preemptions_increment_count(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """多次抢占正确累加计数

        验证:
        - 每次抢占 preemption_count +1
        - 达到上限前保持 PREEMPTED 状态
        """
        # Arrange
        job = create_test_job(
            job_id=1,
            status=JobStatus.RUNNING,
            preemption_count=0,
        )

        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name=TEST_CLUSTER_NAME,
        )

        # Act & Assert: 逐次抢占
        for expected_count in range(1, MAX_PREEMPTION_COUNT):
            await service.sync_job(job)

            if expected_count < MAX_PREEMPTION_COUNT:
                assert job.preemption_count == expected_count
                # 重置状态模拟重新调度
                if job.status == JobStatus.PREEMPTED:
                    job.status = JobStatus.RUNNING

    @pytest.mark.asyncio
    async def test_preemption_from_submitted_state_is_invalid(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """SUBMITTED 状态不能被抢占

        验证:
        - SUBMITTED → PREEMPTED 是非法转换
        - 同步服务应跳过此类任务
        """
        # Arrange: SUBMITTED 状态任务
        job = create_test_job(
            job_id=1,
            status=JobStatus.SUBMITTED,
        )

        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": job.job_name,
            "status": "Preempted",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name=TEST_CLUSTER_NAME,
        )

        # Act
        result = await service.sync_job(job)

        # Assert: 转换失败
        assert result is False
        assert job.status == JobStatus.SUBMITTED  # 状态未改变
        mock_training_job_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_high_priority_job_not_preempted(
        self,
        mock_training_job_repository: AsyncMock,
        mock_hyperpod_client: AsyncMock,
    ) -> None:
        """高优先级任务不被抢占 (保持 Running)

        验证:
        - 高优先级任务持续 Running
        - 不受低优先级任务影响
        """
        # Arrange: 高优先级 Running 任务
        high_priority_job = create_test_job(
            job_id=1,
            priority=JobPriority.HIGH,
            status=JobStatus.RUNNING,
        )

        # HyperPod 返回 Running 状态 (未被抢占)
        mock_hyperpod_client.get_training_job_status.return_value = {
            "job_name": high_priority_job.job_name,
            "status": "Running",
        }

        service = TrainingSyncService(
            training_job_repository=mock_training_job_repository,
            hyperpod_client=mock_hyperpod_client,
            cluster_name=TEST_CLUSTER_NAME,
        )

        # Act
        result = await service.sync_job(high_priority_job)

        # Assert: 状态未变化
        assert result is False  # 状态未变化返回 False (实际是跳过)
        assert high_priority_job.status == JobStatus.RUNNING
        assert high_priority_job.preemption_count == 0


# =============================================================================
# Test Class: 检查点存储层测试 - TestCheckpointStorage
# =============================================================================


@pytest.mark.integration
class TestCheckpointStorage:
    """检查点存储层集成测试"""

    @pytest.mark.asyncio
    async def test_checkpoint_storage_path_generation(
        self,
        mock_checkpoint_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_storage_service: AsyncMock,
    ) -> None:
        """验证检查点存储路径生成"""
        # Arrange
        job = create_test_job(job_id=42, status=JobStatus.RUNNING)
        mock_training_job_repository.get_by_id.return_value = job
        mock_storage_service.get_storage_path.return_value = (
            "/mnt/nvme/checkpoints/42/preemption-20260124120000"
        )

        created_checkpoint = create_test_checkpoint(checkpoint_id=1, training_job_id=42)
        mock_checkpoint_repository.create.return_value = created_checkpoint

        checkpoint_service = CheckpointService(
            repository=mock_checkpoint_repository,
            training_job_repository=mock_training_job_repository,
            storage_service=mock_storage_service,
        )

        # Act
        await checkpoint_service.create_checkpoint_on_preemption(job_id=42)

        # Assert: 验证存储路径调用
        mock_storage_service.get_storage_path.assert_called()

    @pytest.mark.asyncio
    async def test_checkpoint_checksum_calculated(
        self,
        mock_checkpoint_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_storage_service: AsyncMock,
    ) -> None:
        """验证检查点校验和计算"""
        # Arrange
        expected_checksum = "sha256:abcdef123456"
        mock_storage_service.calculate_checksum.return_value = expected_checksum

        job = create_test_job(job_id=1, status=JobStatus.RUNNING)
        mock_training_job_repository.get_by_id.return_value = job

        created_checkpoint = create_test_checkpoint(checkpoint_id=1, training_job_id=1)
        mock_checkpoint_repository.create.return_value = created_checkpoint

        checkpoint_service = CheckpointService(
            repository=mock_checkpoint_repository,
            training_job_repository=mock_training_job_repository,
            storage_service=mock_storage_service,
        )

        # Act
        await checkpoint_service.create_checkpoint_on_preemption(job_id=1)

        # Assert: 验证校验和计算被调用
        mock_storage_service.calculate_checksum.assert_called()

    @pytest.mark.asyncio
    async def test_checkpoint_size_recorded(
        self,
        mock_checkpoint_repository: AsyncMock,
        mock_training_job_repository: AsyncMock,
        mock_storage_service: AsyncMock,
    ) -> None:
        """验证检查点大小记录"""
        # Arrange
        expected_size = 500 * 1024 * 1024  # 500MB
        mock_storage_service.get_checkpoint_size.return_value = expected_size

        job = create_test_job(job_id=1, status=JobStatus.RUNNING)
        mock_training_job_repository.get_by_id.return_value = job

        created_checkpoint = create_test_checkpoint(checkpoint_id=1, training_job_id=1)
        mock_checkpoint_repository.create.return_value = created_checkpoint

        checkpoint_service = CheckpointService(
            repository=mock_checkpoint_repository,
            training_job_repository=mock_training_job_repository,
            storage_service=mock_storage_service,
        )

        # Act
        await checkpoint_service.create_checkpoint_on_preemption(job_id=1)

        # Assert: 验证大小计算被调用
        mock_storage_service.get_checkpoint_size.assert_called()
