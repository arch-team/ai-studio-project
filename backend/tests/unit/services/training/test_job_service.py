"""TrainingJobService单元测试"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from services.training.job_service import TrainingJobService
from models.training import (
    TrainingJob,
    TrainingJobConfig,
    TrainingJobStatus,
    TrainingJobType,
    FrameworkType,
)
from models.user import User, Project
from api.schemas.training import TrainingJobCreate, TrainingJobUpdate, TrainingJobConfigCreate


@pytest.fixture
def mock_session():
    """模拟数据库会话"""
    session = AsyncMock()
    return session


@pytest.fixture
def training_job_service(mock_session):
    """创建TrainingJobService实例"""
    return TrainingJobService(session=mock_session)


@pytest.fixture
def sample_project():
    """示例项目"""
    return Project(
        id=1,
        name="test-project",
        description="Test Project",
    )


@pytest.fixture
def sample_user():
    """示例用户"""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
    )


@pytest.fixture
def sample_training_job_create():
    """示例训练任务创建数据"""
    config = TrainingJobConfigCreate(
        node_count=2,
        gpu_per_node=4,
        cpu_per_node=16,
        memory_per_node_gb=64,
        gpu_type="V100",
        docker_image="pytorch/pytorch:2.0.0",
        command=["python", "train.py"],
        args=["--epochs", "10"],
        env_vars={"CUDA_VISIBLE_DEVICES": "0,1,2,3"},
        dataset_path="/data/train",
        output_path="/output/model",
        hyperparameters={"learning_rate": 0.001, "batch_size": 32},
    )

    return TrainingJobCreate(
        name="test-training-job",
        description="Test Training Job",
        job_type=TrainingJobType.SINGLE_NODE,
        framework=FrameworkType.PYTORCH,
        project_id=1,
        config=config,
    )


@pytest.fixture
def sample_training_job():
    """示例训练任务"""
    job = TrainingJob(
        id=1,
        name="test-training-job",
        description="Test Training Job",
        status=TrainingJobStatus.PENDING,
        job_type=TrainingJobType.SINGLE_NODE,
        framework=FrameworkType.PYTORCH,
        project_id=1,
        creator_id=1,
        k8s_namespace="ai-training-1",
    )

    config = TrainingJobConfig(
        id=1,
        job_id=1,
        node_count=2,
        gpu_per_node=4,
        cpu_per_node=16,
        memory_per_node_gb=64,
        gpu_type="V100",
        docker_image="pytorch/pytorch:2.0.0",
        command=["python", "train.py"],
        args=["--epochs", "10"],
        env_vars={"CUDA_VISIBLE_DEVICES": "0,1,2,3"},
        dataset_path="/data/train",
        output_path="/output/model",
    )

    job.config = config
    return job


class TestCreateTrainingJob:
    """测试创建训练任务"""

    @pytest.mark.asyncio
    async def test_create_training_job_success(
        self,
        training_job_service,
        mock_session,
        sample_training_job_create,
        sample_user,
        sample_project,
    ):
        """测试成功创建训练任务"""
        # 模拟项目查询
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_project
        mock_session.execute.return_value = mock_result

        # 执行创建
        job = await training_job_service.create_training_job(
            job_data=sample_training_job_create,
            creator=sample_user,
        )

        # 验证结果
        assert job.name == "test-training-job"
        assert job.status == TrainingJobStatus.PENDING
        assert job.framework == FrameworkType.PYTORCH
        assert job.creator_id == sample_user.id
        assert job.k8s_namespace == "ai-training-1"

        # 验证数据库操作
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_training_job_project_not_found(
        self,
        training_job_service,
        mock_session,
        sample_training_job_create,
        sample_user,
    ):
        """测试项目不存在时创建失败"""
        # 模拟项目不存在
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # 验证抛出异常
        with pytest.raises(ValueError, match="项目 .* 不存在"):
            await training_job_service.create_training_job(
                job_data=sample_training_job_create,
                creator=sample_user,
            )


class TestGetTrainingJob:
    """测试获取训练任务"""

    @pytest.mark.asyncio
    async def test_get_training_job_success(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试成功获取训练任务"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_training_job
        mock_session.execute.return_value = mock_result

        # 执行查询
        job = await training_job_service.get_training_job(1)

        # 验证结果
        assert job is not None
        assert job.id == 1
        assert job.name == "test-training-job"

    @pytest.mark.asyncio
    async def test_get_training_job_not_found(
        self,
        training_job_service,
        mock_session,
    ):
        """测试训练任务不存在"""
        # 模拟查询无结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # 执行查询
        job = await training_job_service.get_training_job(999)

        # 验证结果
        assert job is None


class TestListTrainingJobs:
    """测试列出训练任务"""

    @pytest.mark.asyncio
    async def test_list_training_jobs_success(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试成功列出训练任务"""
        # 模拟统计查询
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1

        # 模拟列表查询
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [sample_training_job]

        # 配置execute返回不同结果
        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # 执行列表查询
        jobs, total = await training_job_service.list_training_jobs(
            project_id=1,
            page=1,
            size=20,
        )

        # 验证结果
        assert total == 1
        assert len(jobs) == 1
        assert jobs[0].id == 1

    @pytest.mark.asyncio
    async def test_list_training_jobs_with_filters(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试带过滤条件的列表查询"""
        # 模拟查询结果
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [sample_training_job]

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # 执行查询
        jobs, total = await training_job_service.list_training_jobs(
            project_id=1,
            creator_id=1,
            status=TrainingJobStatus.PENDING,
            framework=FrameworkType.PYTORCH,
            page=1,
            size=10,
        )

        # 验证结果
        assert total == 1
        assert len(jobs) == 1


class TestUpdateTrainingJob:
    """测试更新训练任务"""

    @pytest.mark.asyncio
    async def test_update_training_job_success(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试成功更新训练任务"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_training_job
        mock_session.execute.return_value = mock_result

        # 创建更新数据
        update_data = TrainingJobUpdate(
            name="updated-job",
            description="Updated Description",
        )

        # 执行更新
        job = await training_job_service.update_training_job(1, update_data)

        # 验证结果
        assert job is not None
        assert job.name == "updated-job"
        assert job.description == "Updated Description"

        # 验证数据库操作
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_training_job_not_found(
        self,
        training_job_service,
        mock_session,
    ):
        """测试更新不存在的训练任务"""
        # 模拟查询无结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # 创建更新数据
        update_data = TrainingJobUpdate(name="updated-job")

        # 执行更新
        job = await training_job_service.update_training_job(999, update_data)

        # 验证结果
        assert job is None


class TestDeleteTrainingJob:
    """测试删除训练任务"""

    @pytest.mark.asyncio
    async def test_delete_training_job_success(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试成功删除训练任务"""
        # 设置任务为终止状态
        sample_training_job.status = TrainingJobStatus.COMPLETED

        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_training_job
        mock_session.execute.return_value = mock_result

        # 执行删除
        success = await training_job_service.delete_training_job(1)

        # 验证结果
        assert success is True
        assert sample_training_job.is_deleted is True
        assert sample_training_job.deleted_at is not None

        # 验证数据库操作
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_training_job_active_state(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试删除活跃状态的训练任务失败"""
        # 设置任务为运行状态
        sample_training_job.status = TrainingJobStatus.RUNNING

        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_training_job
        mock_session.execute.return_value = mock_result

        # 验证抛出异常
        with pytest.raises(ValueError, match="无法删除活跃状态的任务"):
            await training_job_service.delete_training_job(1)

    @pytest.mark.asyncio
    async def test_delete_training_job_not_found(
        self,
        training_job_service,
        mock_session,
    ):
        """测试删除不存在的训练任务"""
        # 模拟查询无结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # 执行删除
        success = await training_job_service.delete_training_job(999)

        # 验证结果
        assert success is False


class TestStartTrainingJob:
    """测试启动训练任务"""

    @pytest.mark.asyncio
    async def test_start_training_job_success(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试成功启动训练任务"""
        # 确保任务处于PENDING状态
        sample_training_job.status = TrainingJobStatus.PENDING

        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_training_job
        mock_session.execute.return_value = mock_result

        # 执行启动
        job = await training_job_service.start_training_job(1)

        # 验证结果
        assert job.status == TrainingJobStatus.QUEUED
        assert job.queued_at is not None

        # 验证数据库操作
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_training_job_invalid_status(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试启动非PENDING状态的训练任务失败"""
        # 设置任务为运行状态
        sample_training_job.status = TrainingJobStatus.RUNNING

        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_training_job
        mock_session.execute.return_value = mock_result

        # 验证抛出异常
        with pytest.raises(ValueError, match="任务状态 .* 不允许启动"):
            await training_job_service.start_training_job(1)

    @pytest.mark.asyncio
    async def test_start_training_job_not_found(
        self,
        training_job_service,
        mock_session,
    ):
        """测试启动不存在的训练任务"""
        # 模拟查询无结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # 验证抛出异常
        with pytest.raises(ValueError, match="训练任务 .* 不存在"):
            await training_job_service.start_training_job(999)


class TestStopTrainingJob:
    """测试停止训练任务"""

    @pytest.mark.asyncio
    async def test_stop_training_job_success(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试成功停止训练任务"""
        # 设置任务为运行状态
        sample_training_job.status = TrainingJobStatus.RUNNING

        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_training_job
        mock_session.execute.return_value = mock_result

        # 执行停止
        job = await training_job_service.stop_training_job(1)

        # 验证结果
        assert job.status == TrainingJobStatus.CANCELLED
        assert job.completed_at is not None

        # 验证数据库操作
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_training_job_invalid_status(
        self,
        training_job_service,
        mock_session,
        sample_training_job,
    ):
        """测试停止非活跃状态的训练任务失败"""
        # 设置任务为完成状态
        sample_training_job.status = TrainingJobStatus.COMPLETED

        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_training_job
        mock_session.execute.return_value = mock_result

        # 验证抛出异常
        with pytest.raises(ValueError, match="任务状态 .* 不允许停止"):
            await training_job_service.stop_training_job(1)

    @pytest.mark.asyncio
    async def test_stop_training_job_not_found(
        self,
        training_job_service,
        mock_session,
    ):
        """测试停止不存在的训练任务"""
        # 模拟查询无结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # 验证抛出异常
        with pytest.raises(ValueError, match="训练任务 .* 不存在"):
            await training_job_service.stop_training_job(999)
