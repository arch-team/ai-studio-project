"""测试Checkpoint分层存储迁移服务"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.training import (
    Checkpoint,
    CheckpointStorageType,
    TrainingJob,
    TrainingJobStatus,
)
from services.checkpoint.storage_migration_service import StorageMigrationService


@pytest.fixture
def mock_s3_service():
    """Mock S3MigrationService"""
    with patch(
        "services.checkpoint.storage_migration_service.S3MigrationService"
    ) as mock:
        instance = mock.return_value
        instance.migrate_to_s3 = AsyncMock(return_value="s3://bucket/key")
        yield instance


@pytest.fixture
async def test_training_job(test_db_session: AsyncSession):
    """创建测试训练任务"""
    job = TrainingJob(
        name="test-job",
        project_id=1,
        created_by=1,
        framework="pytorch",
        status=TrainingJobStatus.RUNNING,
    )
    test_db_session.add(job)
    await test_db_session.commit()
    await test_db_session.refresh(job)
    return job


@pytest.fixture
async def test_checkpoint_nvme(
    test_db_session: AsyncSession, test_training_job: TrainingJob
):
    """创建NVMe上的测试checkpoint"""
    checkpoint = Checkpoint(
        job_id=test_training_job.id,
        step=100,
        storage_path="/mnt/nvme/checkpoints/1/step-100.pt",
        storage_type=CheckpointStorageType.LOCAL,
        size_bytes=1024 * 1024,  # 1MB
        created_at=datetime.utcnow() - timedelta(days=10),  # 10天前
    )
    test_db_session.add(checkpoint)
    await test_db_session.commit()
    await test_db_session.refresh(checkpoint)
    return checkpoint


@pytest.fixture
async def test_checkpoint_fsx(
    test_db_session: AsyncSession, test_training_job: TrainingJob
):
    """创建FSx上的测试checkpoint"""
    checkpoint = Checkpoint(
        job_id=test_training_job.id,
        step=200,
        storage_path="/mnt/fsx/checkpoints/1/step-200.pt",
        storage_type=CheckpointStorageType.FSX,
        size_bytes=2 * 1024 * 1024,  # 2MB
        created_at=datetime.utcnow() - timedelta(days=35),  # 35天前
    )
    test_db_session.add(checkpoint)
    await test_db_session.commit()
    await test_db_session.refresh(checkpoint)
    return checkpoint


class TestStorageMigrationService:
    """测试StorageMigrationService"""

    @pytest.mark.asyncio
    async def test_migrate_nvme_to_fsx_success(
        self,
        test_db_session: AsyncSession,
        test_checkpoint_nvme: Checkpoint,
    ):
        """测试NVMe→FSx迁移成功"""
        service = StorageMigrationService(test_db_session)

        # Mock文件操作
        with patch("pathlib.Path.unlink") as mock_unlink, patch(
            "shutil.copy2"
        ) as mock_copy:
            success = await service.migrate_nvme_to_fsx(
                test_checkpoint_nvme, delete_source=True
            )

            assert success is True
            # 验证数据库更新
            await test_db_session.refresh(test_checkpoint_nvme)
            assert test_checkpoint_nvme.storage_type == CheckpointStorageType.FSX
            assert "/mnt/fsx/checkpoints" in test_checkpoint_nvme.storage_path

            # 验证文件操作
            mock_copy.assert_called_once()
            mock_unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_migrate_nvme_to_fsx_skip_non_nvme(
        self,
        test_db_session: AsyncSession,
        test_checkpoint_fsx: Checkpoint,
    ):
        """测试跳过非NVMe checkpoint"""
        service = StorageMigrationService(test_db_session)

        success = await service.migrate_nvme_to_fsx(test_checkpoint_fsx)

        assert success is False
        # 验证存储类型未改变
        await test_db_session.refresh(test_checkpoint_fsx)
        assert test_checkpoint_fsx.storage_type == CheckpointStorageType.FSX

    @pytest.mark.asyncio
    async def test_migrate_fsx_to_s3_success(
        self,
        test_db_session: AsyncSession,
        test_checkpoint_fsx: Checkpoint,
        mock_s3_service,
    ):
        """测试FSx→S3迁移成功"""
        service = StorageMigrationService(test_db_session)
        service.s3_service = mock_s3_service

        success = await service.migrate_fsx_to_s3(
            test_checkpoint_fsx, delete_source=True
        )

        assert success is True
        # 验证数据库更新
        await test_db_session.refresh(test_checkpoint_fsx)
        assert test_checkpoint_fsx.storage_type == CheckpointStorageType.S3
        assert test_checkpoint_fsx.storage_path.startswith("s3://")

        # 验证S3服务调用
        mock_s3_service.migrate_to_s3.assert_called_once()

    @pytest.mark.asyncio
    async def test_migrate_fsx_to_s3_skip_non_fsx(
        self,
        test_db_session: AsyncSession,
        test_checkpoint_nvme: Checkpoint,
        mock_s3_service,
    ):
        """测试跳过非FSx checkpoint"""
        service = StorageMigrationService(test_db_session)
        service.s3_service = mock_s3_service

        success = await service.migrate_fsx_to_s3(test_checkpoint_nvme)

        assert success is False
        # 验证存储类型未改变
        await test_db_session.refresh(test_checkpoint_nvme)
        assert test_checkpoint_nvme.storage_type == CheckpointStorageType.LOCAL

    @pytest.mark.asyncio
    async def test_get_old_checkpoints(
        self,
        test_db_session: AsyncSession,
        test_checkpoint_nvme: Checkpoint,
    ):
        """测试查询旧checkpoint"""
        service = StorageMigrationService(test_db_session)

        # 查询7天以前的NVMe checkpoint
        old_checkpoints = await service._get_old_checkpoints(
            storage_type=CheckpointStorageType.LOCAL, older_than_days=7
        )

        assert len(old_checkpoints) == 1
        assert old_checkpoints[0].id == test_checkpoint_nvme.id

        # 查询15天以前的checkpoint (应该为空,因为只有10天前的)
        very_old_checkpoints = await service._get_old_checkpoints(
            storage_type=CheckpointStorageType.LOCAL, older_than_days=15
        )

        assert len(very_old_checkpoints) == 0

    @pytest.mark.asyncio
    async def test_get_last_checkpoints_of_completed_jobs(
        self,
        test_db_session: AsyncSession,
        test_training_job: TrainingJob,
    ):
        """测试获取已完成任务的最后checkpoint"""
        # 创建多个checkpoint
        checkpoints = []
        for step in [100, 200, 300]:
            ckpt = Checkpoint(
                job_id=test_training_job.id,
                step=step,
                storage_path=f"/mnt/nvme/checkpoints/1/step-{step}.pt",
                storage_type=CheckpointStorageType.LOCAL,
                size_bytes=1024 * 1024,
            )
            test_db_session.add(ckpt)
            checkpoints.append(ckpt)

        # 标记任务为完成
        test_training_job.status = TrainingJobStatus.COMPLETED
        await test_db_session.commit()

        service = StorageMigrationService(test_db_session)
        last_checkpoints = await service._get_last_checkpoints_of_completed_jobs()

        # 应该只返回step=300的最后checkpoint
        assert len(last_checkpoints) == 1
        assert last_checkpoints[0].step == 300

    @pytest.mark.asyncio
    async def test_run_migration_policy(
        self,
        test_db_session: AsyncSession,
        test_checkpoint_nvme: Checkpoint,
        test_checkpoint_fsx: Checkpoint,
        mock_s3_service,
    ):
        """测试完整迁移策略"""
        service = StorageMigrationService(test_db_session)
        service.s3_service = mock_s3_service

        # Mock文件操作
        with patch("pathlib.Path.unlink"), patch("shutil.copy2"):
            stats = await service.run_migration_policy()

            # 验证统计信息
            assert "nvme_to_fsx" in stats
            assert "fsx_to_s3" in stats
            assert "errors" in stats

            # NVMe checkpoint应该迁移到FSx (10天前,超过7天阈值)
            assert stats["nvme_to_fsx"] >= 1

            # FSx checkpoint应该迁移到S3 (35天前,超过30天阈值)
            assert stats["fsx_to_s3"] >= 1

    @pytest.mark.asyncio
    async def test_generate_fsx_path(
        self,
        test_db_session: AsyncSession,
        test_checkpoint_nvme: Checkpoint,
    ):
        """测试生成FSx路径"""
        service = StorageMigrationService(test_db_session)

        fsx_path = service._generate_fsx_path(test_checkpoint_nvme)

        assert "/mnt/fsx/checkpoints" in fsx_path
        assert f"/{test_checkpoint_nvme.job_id}/" in fsx_path
        assert f"step-{test_checkpoint_nvme.step}.pt" in fsx_path

    @pytest.mark.asyncio
    async def test_migrate_fsx_to_s3_error_handling(
        self,
        test_db_session: AsyncSession,
        test_checkpoint_fsx: Checkpoint,
        mock_s3_service,
    ):
        """测试FSx→S3迁移错误处理"""
        service = StorageMigrationService(test_db_session)
        service.s3_service = mock_s3_service

        # Mock S3服务抛出异常
        mock_s3_service.migrate_to_s3.side_effect = Exception("S3 upload failed")

        success = await service.migrate_fsx_to_s3(test_checkpoint_fsx)

        assert success is False
        # 验证数据库未更新(回滚)
        await test_db_session.refresh(test_checkpoint_fsx)
        assert test_checkpoint_fsx.storage_type == CheckpointStorageType.FSX
