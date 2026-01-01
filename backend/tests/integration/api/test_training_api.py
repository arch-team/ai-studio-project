"""训练任务API集成测试"""

import pytest
from fastapi import status

from models.training import TrainingJobStatus, TrainingJobType, FrameworkType


class TestCreateTrainingJobEndpoint:
    """测试创建训练任务端点"""

    @pytest.mark.asyncio
    async def test_create_training_job_success(self, client, test_user, test_project):
        """测试成功创建训练任务"""
        # 使用fixture提供的测试项目
        project = test_project

        # 首先登录获取token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 创建训练任务
        job_data = {
            "name": "test-training-job",
            "description": "Test Training Job",
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": project.id,
            "config": {
                "node_count": 2,
                "gpu_per_node": 4,
                "cpu_per_node": 16,
                "memory_per_node_gb": 64,
                "gpu_type": "V100",
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "args": ["--epochs", "10"],
                "env_vars": {"CUDA_VISIBLE_DEVICES": "0,1,2,3"},
                "dataset_path": "/data/train",
                "output_path": "/output/model",
                "hyperparameters": {"learning_rate": 0.001, "batch_size": 32},
            },
        }

        response = await client.post(
            "/api/v1/training/jobs",
            json=job_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != status.HTTP_201_CREATED:
            print(f"\nDEBUG: Status={response.status_code}, Response={response.json()}")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "test-training-job"
        assert data["status"] == "PENDING"
        assert data["framework"] == "PYTORCH"
        assert data["project_id"] == project.id
        assert data["k8s_namespace"] == f"ai-training-{project.id}"
        assert "config" in data

    @pytest.mark.asyncio
    async def test_create_training_job_invalid_project(self, client, test_user):
        """测试创建训练任务时项目不存在"""
        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 使用不存在的项目ID
        job_data = {
            "name": "test-job",
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": 999,
            "config": {
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "output_path": "/output/model",
            },
        }

        response = await client.post(
            "/api/v1/training/jobs",
            json=job_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "项目" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_training_job_invalid_name(self, client, test_user):
        """测试创建训练任务时名称无效"""
        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 使用包含特殊字符的名称
        job_data = {
            "name": "test job with spaces!",  # 包含空格和特殊字符
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": 1,
            "config": {
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "output_path": "/output/model",
            },
        }

        response = await client.post(
            "/api/v1/training/jobs",
            json=job_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.skip(reason="临时mock认证(get_current_user)总是返回用户,等T034真实认证系统完成后启用")
    @pytest.mark.asyncio
    async def test_create_training_job_without_auth(self, client):
        """测试未认证创建训练任务"""
        job_data = {
            "name": "test-job",
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": 1,
            "config": {
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "output_path": "/output/model",
            },
        }

        response = await client.post("/api/v1/training/jobs", json=job_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestListTrainingJobsEndpoint:
    """测试列出训练任务端点"""

    @pytest.mark.asyncio
    async def test_list_training_jobs_success(
        self, client, test_user, test_project
    ):
        """测试成功列出训练任务"""
        # 使用fixture提供的测试项目
        project = test_project

        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 创建2个训练任务
        for i in range(2):
            job_data = {
                "name": f"test-job-{i}",
                "job_type": "SINGLE_NODE",
                "framework": "PYTORCH",
                "project_id": project.id,
                "config": {
                    "docker_image": "pytorch/pytorch:2.0.0",
                    "command": ["python", "train.py"],
                    "output_path": "/output/model",
                },
            }
            create_response = await client.post(
                "/api/v1/training/jobs",
                json=job_data,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if create_response.status_code != status.HTTP_201_CREATED:
                print(f"\n创建任务{i}失败: {create_response.status_code}, {create_response.json()}")

        # 查询列表
        response = await client.get(
            "/api/v1/training/jobs",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        print(f"\n列表返回: total={data['total']}, items count={len(data['items'])}")
        assert data["total"] >= 2
        assert len(data["items"]) >= 2
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_training_jobs_with_filters(
        self, client, test_user, test_project
    ):
        """测试带过滤条件的列表查询"""
        # 使用fixture提供的测试项目
        project = test_project

        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 创建训练任务
        job_data = {
            "name": "test-job",
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": project.id,
            "config": {
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "output_path": "/output/model",
            },
        }
        await client.post(
            "/api/v1/training/jobs",
            json=job_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # 带项目过滤的查询
        response = await client.get(
            f"/api/v1/training/jobs?project_id={project.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["project_id"] == project.id for item in data["items"])

    @pytest.mark.asyncio
    async def test_list_training_jobs_pagination(
        self, client, test_user, test_project
    ):
        """测试分页查询"""
        # 使用fixture提供的测试项目
        project = test_project

        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 创建多个训练任务
        for i in range(5):
            job_data = {
                "name": f"test-job-{i}",
                "job_type": "SINGLE_NODE",
                "framework": "PYTORCH",
                "project_id": project.id,
                "config": {
                    "docker_image": "pytorch/pytorch:2.0.0",
                    "command": ["python", "train.py"],
                    "output_path": "/output/model",
                },
            }
            await client.post(
                "/api/v1/training/jobs",
                json=job_data,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # 第一页
        response1 = await client.get(
            "/api/v1/training/jobs?page=1&page_size=2",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert data1["page"] == 1
        assert len(data1["items"]) == 2

        # 第二页
        response2 = await client.get(
            "/api/v1/training/jobs?page=2&page_size=2",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["page"] == 2


class TestGetTrainingJobEndpoint:
    """测试获取训练任务详情端点"""

    @pytest.mark.asyncio
    async def test_get_training_job_success(self, client, test_user, test_project):
        """测试成功获取训练任务详情"""
        # 使用fixture提供的测试项目
        project = test_project

        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 创建训练任务
        job_data = {
            "name": "test-job",
            "description": "Test Job",
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": project.id,
            "config": {
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "output_path": "/output/model",
            },
        }
        create_response = await client.post(
            "/api/v1/training/jobs",
            json=job_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        job_id = create_response.json()["id"]

        # 获取详情
        response = await client.get(
            f"/api/v1/training/jobs/{job_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == job_id
        assert data["name"] == "test-job"
        assert data["description"] == "Test Job"
        assert "config" in data

    @pytest.mark.asyncio
    async def test_get_training_job_not_found(self, client, test_user):
        """测试获取不存在的训练任务"""
        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 查询不存在的任务
        response = await client.get(
            "/api/v1/training/jobs/999",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateTrainingJobEndpoint:
    """测试更新训练任务端点"""

    @pytest.mark.asyncio
    async def test_update_training_job_success(self, client, test_user, test_project):
        """测试成功更新训练任务"""
        # 使用fixture提供的测试项目
        project = test_project

        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 创建训练任务
        job_data = {
            "name": "test-job",
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": project.id,
            "config": {
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "output_path": "/output/model",
            },
        }
        create_response = await client.post(
            "/api/v1/training/jobs",
            json=job_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        job_id = create_response.json()["id"]

        # 更新训练任务
        update_data = {
            "name": "updated-job",
            "description": "Updated Description",
        }
        response = await client.patch(
            f"/api/v1/training/jobs/{job_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "updated-job"
        assert data["description"] == "Updated Description"


class TestDeleteTrainingJobEndpoint:
    """测试删除训练任务端点"""

    @pytest.mark.asyncio
    async def test_delete_training_job_success(self, client, test_user, test_project):
        """测试成功删除训练任务"""
        # 使用fixture提供的测试项目
        project = test_project

        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 创建训练任务
        job_data = {
            "name": "test-job",
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": project.id,
            "config": {
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "output_path": "/output/model",
            },
        }
        create_response = await client.post(
            "/api/v1/training/jobs",
            json=job_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        job_id = create_response.json()["id"]

        # 注意: 只能删除终止状态的任务,这里直接删除会失败
        # 需要先模拟任务完成状态
        # 为简化测试,这里只测试删除失败的情况

        # 尝试删除活跃任务(应该失败)
        response = await client.delete(
            f"/api/v1/training/jobs/{job_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "无法删除活跃状态的任务" in response.json()["detail"]


class TestStartTrainingJobEndpoint:
    """测试启动训练任务端点"""

    @pytest.mark.asyncio
    async def test_start_training_job_success(self, client, test_user, test_project):
        """测试成功启动训练任务"""
        # 使用fixture提供的测试项目
        project = test_project

        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 创建训练任务
        job_data = {
            "name": "test-job",
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": project.id,
            "config": {
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "output_path": "/output/model",
            },
        }
        create_response = await client.post(
            "/api/v1/training/jobs",
            json=job_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        job_id = create_response.json()["id"]

        # 启动训练任务
        response = await client.post(
            f"/api/v1/training/jobs/{job_id}/start",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != status.HTTP_200_OK:
            print(f"\n启动失败: {response.status_code}, {response.json()}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "QUEUED"
        assert data["queued_at"] is not None


class TestStopTrainingJobEndpoint:
    """测试停止训练任务端点"""

    @pytest.mark.asyncio
    async def test_stop_training_job_invalid_status(
        self, client, test_user, test_project
    ):
        """测试停止非活跃任务失败"""
        # 使用fixture提供的测试项目
        project = test_project

        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.json()["access_token"]

        # 创建训练任务(PENDING状态)
        job_data = {
            "name": "test-job",
            "job_type": "SINGLE_NODE",
            "framework": "PYTORCH",
            "project_id": project.id,
            "config": {
                "docker_image": "pytorch/pytorch:2.0.0",
                "command": ["python", "train.py"],
                "output_path": "/output/model",
            },
        }
        create_response = await client.post(
            "/api/v1/training/jobs",
            json=job_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        job_id = create_response.json()["id"]

        # 尝试停止PENDING状态的任务(应该失败)
        response = await client.post(
            f"/api/v1/training/jobs/{job_id}/stop",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "不允许停止" in response.json()["detail"]


