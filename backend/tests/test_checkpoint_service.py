"""Checkpoint服务单元测试"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.training import CheckpointStorageType, TrainingJob, TrainingJobConfig
from models.user import Project, Team, User
from services.checkpoint import CheckpointService


@pytest.fixture
async def test_user(test_db_session: AsyncSession) -> User:
    """创建测试用户"""
    user = User(username="test_user", email="test@example.com", hashed_password="hashed")
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def test_team(test_db_session: AsyncSession, test_user: User) -> Team:
    """创建测试团队"""
    team = Team(name="test_team", description="Test team", owner_id=test_user.id)
    test_db_session.add(team)
    await test_db_session.commit()
    await test_db_session.refresh(team)
    return team


@pytest.fixture
async def test_project(
    test_db_session: AsyncSession, test_team: Team, test_user: User
) -> Project:
    """创建测试项目"""
    project = Project(
        name="test_project",
        description="Test project",
        team_id=test_team.id,
        creator_id=test_user.id,
    )
    test_db_session.add(project)
    await test_db_session.commit()
    await test_db_session.refresh(project)
    return project


@pytest.fixture
async def test_training_job(
    test_db_session: AsyncSession, test_project: Project, test_user: User
) -> TrainingJob:
    """创建测试训练任务"""
    from models.training import FrameworkType, TrainingJobStatus, TrainingJobType

    job = TrainingJob(
        name="test_job",
        description="Test training job",
        project_id=test_project.id,
        creator_id=test_user.id,
        status=TrainingJobStatus.RUNNING,
        job_type=TrainingJobType.SINGLE_NODE,
        framework=FrameworkType.PYTORCH,
        k8s_namespace="default",
    )
    test_db_session.add(job)
    await test_db_session.commit()
    await test_db_session.refresh(job)

    # 添加配置
    config = TrainingJobConfig(
        job_id=job.id,
        node_count=1,
        gpu_per_node=1,
        docker_image="pytorch/pytorch:2.0.0",
        command=["python", "train.py"],
        output_path="/output",
    )
    test_db_session.add(config)
    await test_db_session.commit()

    return job


class TestCheckpointService:
    """CheckpointService测试类"""

    async def test_register_checkpoint(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试注册checkpoint"""
        service = CheckpointService(test_db_session)

        checkpoint = await service.register_checkpoint(
            job_id=test_training_job.id,
            step=1000,
            storage_path="/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
            storage_type=CheckpointStorageType.LOCAL,
            size_bytes=1048576000,
            epoch=5,
            metadata={"learning_rate": 0.001, "optimizer": "AdamW"},
            metrics={"loss": 0.25, "accuracy": 0.92},
        )

        assert checkpoint.id is not None
        assert checkpoint.job_id == test_training_job.id
        assert checkpoint.step == 1000
        assert checkpoint.epoch == 5
        assert checkpoint.storage_type == CheckpointStorageType.LOCAL
        assert checkpoint.size_bytes == 1048576000
        assert checkpoint.checkpoint_metadata["learning_rate"] == 0.001
        assert checkpoint.checkpoint_metrics["loss"] == 0.25

    async def test_register_checkpoint_invalid_job(
        self, test_db_session: AsyncSession
    ):
        """测试注册checkpoint - 无效任务ID"""
        service = CheckpointService(test_db_session)

        with pytest.raises(ValueError, match="训练任务不存在"):
            await service.register_checkpoint(
                job_id=99999,  # 不存在的job_id
                step=1000,
                storage_path="/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
                storage_type=CheckpointStorageType.LOCAL,
                size_bytes=1048576000,
            )

    async def test_list_checkpoints(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试列举checkpoint"""
        service = CheckpointService(test_db_session)

        # 创建多个checkpoint
        for i in range(5):
            await service.register_checkpoint(
                job_id=test_training_job.id,
                step=1000 * (i + 1),
                storage_path=f"/mnt/nvme/checkpoints/1/checkpoint-step-{1000 * (i + 1)}.pt",
                storage_type=CheckpointStorageType.LOCAL,
                size_bytes=1048576000,
            )

        # 列举所有checkpoint
        checkpoints = await service.list_checkpoints(job_id=test_training_job.id)
        assert len(checkpoints) == 5
        # 验证按step降序排列
        assert checkpoints[0].step == 5000
        assert checkpoints[4].step == 1000

    async def test_list_checkpoints_with_storage_filter(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试按存储类型过滤checkpoint"""
        service = CheckpointService(test_db_session)

        # 创建不同存储类型的checkpoint
        await service.register_checkpoint(
            job_id=test_training_job.id,
            step=1000,
            storage_path="/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
            storage_type=CheckpointStorageType.LOCAL,
            size_bytes=1048576000,
        )
        await service.register_checkpoint(
            job_id=test_training_job.id,
            step=2000,
            storage_path="/mnt/fsx/checkpoints/1/checkpoint-step-2000.pt",
            storage_type=CheckpointStorageType.FSX,
            size_bytes=1048576000,
        )
        await service.register_checkpoint(
            job_id=test_training_job.id,
            step=3000,
            storage_path="s3://bucket/checkpoints/1/checkpoint-step-3000.pt",
            storage_type=CheckpointStorageType.S3,
            size_bytes=1048576000,
        )

        # 只查询LOCAL类型
        local_checkpoints = await service.list_checkpoints(
            job_id=test_training_job.id, storage_type=CheckpointStorageType.LOCAL
        )
        assert len(local_checkpoints) == 1
        assert local_checkpoints[0].storage_type == CheckpointStorageType.LOCAL

        # 只查询S3类型
        s3_checkpoints = await service.list_checkpoints(
            job_id=test_training_job.id, storage_type=CheckpointStorageType.S3
        )
        assert len(s3_checkpoints) == 1
        assert s3_checkpoints[0].storage_type == CheckpointStorageType.S3

    async def test_get_latest_checkpoint(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试获取最新checkpoint"""
        service = CheckpointService(test_db_session)

        # 创建多个checkpoint
        await service.register_checkpoint(
            job_id=test_training_job.id,
            step=1000,
            storage_path="/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
            storage_type=CheckpointStorageType.LOCAL,
            size_bytes=1048576000,
        )
        await service.register_checkpoint(
            job_id=test_training_job.id,
            step=2000,
            storage_path="/mnt/nvme/checkpoints/1/checkpoint-step-2000.pt",
            storage_type=CheckpointStorageType.LOCAL,
            size_bytes=1048576000,
        )

        # 获取最新checkpoint
        latest = await service.get_latest_checkpoint(job_id=test_training_job.id)
        assert latest is not None
        assert latest.step == 2000  # 最新的step

    async def test_get_latest_checkpoint_no_results(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试获取最新checkpoint - 无结果"""
        service = CheckpointService(test_db_session)

        latest = await service.get_latest_checkpoint(job_id=test_training_job.id)
        assert latest is None

    async def test_get_checkpoint_by_step(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试根据step获取checkpoint"""
        service = CheckpointService(test_db_session)

        await service.register_checkpoint(
            job_id=test_training_job.id,
            step=1000,
            storage_path="/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
            storage_type=CheckpointStorageType.LOCAL,
            size_bytes=1048576000,
        )

        checkpoint = await service.get_checkpoint_by_step(
            job_id=test_training_job.id, step=1000
        )
        assert checkpoint is not None
        assert checkpoint.step == 1000

    async def test_delete_checkpoint(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试删除checkpoint"""
        service = CheckpointService(test_db_session)

        checkpoint = await service.register_checkpoint(
            job_id=test_training_job.id,
            step=1000,
            storage_path="/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
            storage_type=CheckpointStorageType.LOCAL,
            size_bytes=1048576000,
        )

        # 删除checkpoint
        success = await service.delete_checkpoint(checkpoint.id)
        assert success is True

        # 验证已删除
        deleted_checkpoint = await service.get_checkpoint_by_id(checkpoint.id)
        assert deleted_checkpoint is None

    async def test_delete_checkpoint_not_exists(
        self, test_db_session: AsyncSession
    ):
        """测试删除不存在的checkpoint"""
        service = CheckpointService(test_db_session)

        success = await service.delete_checkpoint(99999)
        assert success is False

    async def test_delete_old_checkpoints(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试删除旧checkpoint(保留最近N个)"""
        service = CheckpointService(test_db_session)

        # 创建10个checkpoint
        for i in range(10):
            await service.register_checkpoint(
                job_id=test_training_job.id,
                step=1000 * (i + 1),
                storage_path=f"/mnt/nvme/checkpoints/1/checkpoint-step-{1000 * (i + 1)}.pt",
                storage_type=CheckpointStorageType.LOCAL,
                size_bytes=1048576000,
            )

        # 保留最近5个,删除其余
        deleted_count = await service.delete_old_checkpoints(
            job_id=test_training_job.id, keep_last_n=5
        )
        assert deleted_count == 5  # 应该删除5个

        # 验证只剩5个
        remaining = await service.list_checkpoints(job_id=test_training_job.id)
        assert len(remaining) == 5
        # 验证保留的是最新的5个
        assert remaining[0].step == 10000
        assert remaining[4].step == 6000

    async def test_delete_old_checkpoints_not_enough(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试删除旧checkpoint - checkpoint数量不足"""
        service = CheckpointService(test_db_session)

        # 只创建3个checkpoint
        for i in range(3):
            await service.register_checkpoint(
                job_id=test_training_job.id,
                step=1000 * (i + 1),
                storage_path=f"/mnt/nvme/checkpoints/1/checkpoint-step-{1000 * (i + 1)}.pt",
                storage_type=CheckpointStorageType.LOCAL,
                size_bytes=1048576000,
            )

        # 保留最近5个(实际只有3个)
        deleted_count = await service.delete_old_checkpoints(
            job_id=test_training_job.id, keep_last_n=5
        )
        assert deleted_count == 0  # 无需删除

        # 验证还是3个
        remaining = await service.list_checkpoints(job_id=test_training_job.id)
        assert len(remaining) == 3

    async def test_delete_old_checkpoints_with_storage_filter(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试按存储类型清理旧checkpoint"""
        service = CheckpointService(test_db_session)

        # 创建LOCAL类型的10个checkpoint
        for i in range(10):
            await service.register_checkpoint(
                job_id=test_training_job.id,
                step=1000 * (i + 1),
                storage_path=f"/mnt/nvme/checkpoints/1/checkpoint-step-{1000 * (i + 1)}.pt",
                storage_type=CheckpointStorageType.LOCAL,
                size_bytes=1048576000,
            )

        # 创建S3类型的3个checkpoint
        for i in range(3):
            await service.register_checkpoint(
                job_id=test_training_job.id,
                step=20000 + 1000 * (i + 1),
                storage_path=f"s3://bucket/checkpoints/1/checkpoint-step-{20000 + 1000 * (i + 1)}.pt",
                storage_type=CheckpointStorageType.S3,
                size_bytes=1048576000,
            )

        # 只清理LOCAL类型,保留最近3个
        deleted_count = await service.delete_old_checkpoints(
            job_id=test_training_job.id,
            keep_last_n=3,
            storage_type=CheckpointStorageType.LOCAL,
        )
        assert deleted_count == 7  # LOCAL类型删除7个

        # 验证LOCAL只剩3个
        local_remaining = await service.list_checkpoints(
            job_id=test_training_job.id, storage_type=CheckpointStorageType.LOCAL
        )
        assert len(local_remaining) == 3

        # 验证S3类型不受影响,还是3个
        s3_remaining = await service.list_checkpoints(
            job_id=test_training_job.id, storage_type=CheckpointStorageType.S3
        )
        assert len(s3_remaining) == 3

    async def test_count_checkpoints(
        self, test_db_session: AsyncSession, test_training_job: TrainingJob
    ):
        """测试统计checkpoint数量"""
        service = CheckpointService(test_db_session)

        # 创建5个checkpoint
        for i in range(5):
            await service.register_checkpoint(
                job_id=test_training_job.id,
                step=1000 * (i + 1),
                storage_path=f"/mnt/nvme/checkpoints/1/checkpoint-step-{1000 * (i + 1)}.pt",
                storage_type=CheckpointStorageType.LOCAL,
                size_bytes=1048576000,
            )

        count = await service.count_checkpoints(job_id=test_training_job.id)
        assert count == 5

    def test_generate_checkpoint_path(self):
        """测试生成checkpoint存储路径"""
        # 不需要数据库会话,可以直接测试
        from sqlalchemy.ext.asyncio import AsyncSession
        from unittest.mock import MagicMock

        mock_session = MagicMock(spec=AsyncSession)
        service = CheckpointService(mock_session)

        # 测试LOCAL路径
        local_path = service.generate_checkpoint_path(
            job_id=1,
            step=1000,
            storage_type=CheckpointStorageType.LOCAL,
            local_dir="/mnt/nvme/checkpoints",
        )
        assert local_path == "/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt"

        # 测试FSX路径
        fsx_path = service.generate_checkpoint_path(
            job_id=1,
            step=1000,
            storage_type=CheckpointStorageType.FSX,
            fsx_dir="/mnt/fsx/checkpoints",
        )
        assert fsx_path == "/mnt/fsx/checkpoints/1/checkpoint-step-1000.pt"

        # 测试S3 URI
        s3_uri = service.generate_checkpoint_path(
            job_id=1,
            step=1000,
            storage_type=CheckpointStorageType.S3,
            s3_bucket="my-bucket",
        )
        assert s3_uri == "s3://my-bucket/checkpoints/1/checkpoint-step-1000.pt"
