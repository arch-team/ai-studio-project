"""AWS E2E 测试配置和 Fixture"""

import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import boto3
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from tests.e2e.config import get_e2e_settings
from tests.shared.constants import TEST_API_BASE_URL

# 配置实例
settings = get_e2e_settings()


# =============================================================================
# Skip 条件检查
# =============================================================================


def _has_aws_credentials() -> bool:
    """检查 AWS 凭证"""
    try:
        boto3.client("sts").get_caller_identity()
        return True
    except Exception:
        return False


def _has_task_governance() -> bool:
    """检查 Task Governance 配置"""
    if not settings.hyperpod_cluster_name:
        return False

    try:
        sagemaker = boto3.client("sagemaker")
        clusters = sagemaker.list_clusters(NameContains=settings.hyperpod_cluster_name)

        if not clusters.get("ClusterSummaries"):
            return False

        cluster_arn = clusters["ClusterSummaries"][0]["ClusterArn"]

        # 检查 Scheduler Config 和 Compute Quotas
        has_scheduler = bool(
            sagemaker.list_cluster_scheduler_configs(ClusterArn=cluster_arn).get("ClusterSchedulerConfigSummaries")
        )
        has_quotas = bool(sagemaker.list_compute_quotas(ClusterArn=cluster_arn).get("ComputeQuotaSummaries"))

        return has_scheduler and has_quotas
    except Exception:
        return False


# Skip 装饰器
skip_without_aws = pytest.mark.skipif(
    not _has_aws_credentials(),
    reason="AWS credentials not configured",
)

skip_without_hyperpod = pytest.mark.skipif(
    not settings.hyperpod_cluster_name,
    reason="HyperPod cluster not configured",
)

skip_without_sso = pytest.mark.skipif(
    False,  # SSO 测试默认允许（测试降级逻辑）
    reason="SSO IdP not configured",
)

skip_write_tests = pytest.mark.skipif(
    settings.e2e_read_only,
    reason="Write tests disabled",
)

skip_without_task_governance = pytest.mark.skipif(
    not _has_task_governance(),
    reason="Task Governance not configured",
)


# =============================================================================
# SLA 常量（直接使用配置）
# =============================================================================


class SLAConstants:
    """SLA 时间窗口（秒）"""

    CHECKPOINT_SAVE_TIMEOUT = settings.sla_checkpoint_save_timeout
    POD_RELEASE_TIMEOUT = settings.sla_pod_release_timeout
    SSO_FAILOVER_TIMEOUT = settings.sla_sso_failover_timeout
    SSO_RECOVERY_CHECK_INTERVAL = settings.sla_sso_recovery_check_interval
    JOB_SUBMISSION_TIMEOUT = settings.sla_job_submission_timeout
    JOB_STATUS_POLL_INTERVAL = settings.sla_job_status_poll_interval
    MAX_PREEMPTION_COUNT = settings.sla_max_preemption_count


# =============================================================================
# AWS 客户端 Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def aws_region() -> str:
    """AWS 区域"""
    return settings.aws_region


@pytest.fixture(scope="session")
def hyperpod_cluster_name() -> str:
    """HyperPod 集群名称"""
    return settings.hyperpod_cluster_name


@pytest.fixture(scope="session")
def sagemaker_client(aws_region: str):
    """SageMaker 客户端"""
    return boto3.client("sagemaker", region_name=aws_region)


@pytest.fixture(scope="session")
def s3_client(aws_region: str):
    """S3 客户端"""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="function")
def hyperpod_client(hyperpod_cluster_name: str, aws_region: str) -> Any:
    """HyperPod 客户端（延迟导入）"""
    try:
        from src.modules.training.infrastructure.hyperpod.client import HyperPodClient

        client = HyperPodClient(region=aws_region)
        client._cluster_name = hyperpod_cluster_name
        return client
    except (ImportError, Exception) as e:
        pytest.skip(f"HyperPodClient unavailable: {e}")


# =============================================================================
# HTTP 客户端 Fixtures
# =============================================================================


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """异步 HTTP 客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=TEST_API_BASE_URL,
        timeout=60.0,
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def admin_token(async_client: AsyncClient) -> str:
    """管理员 Token"""
    if not settings.e2e_admin_password:
        pytest.skip("Admin password not configured")

    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.e2e_admin_username,
            "password": settings.e2e_admin_password,
        },
    )

    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")

    data = response.json()
    return data.get("tokens", data).get("access_token")


# =============================================================================
# 测试配置 Fixtures
# =============================================================================


@pytest.fixture
def test_local_user() -> dict[str, str]:
    """测试用户配置"""
    return {
        "username": settings.e2e_test_username,
        "password": settings.e2e_test_password,
        "email": settings.e2e_test_email,
    }


@pytest.fixture
def sso_health_endpoint() -> str:
    """SSO 健康检查端点"""
    return settings.sso_health_endpoint


def _create_job_config(priority: str, job_type: str, command: list[str]) -> dict[str, Any]:
    """创建任务配置的辅助函数"""
    is_low_priority = priority == "low"

    return {
        "job_name": f"e2e-{job_type}-{int(time.time())}",
        "image_uri": settings.resolved_image_uri,
        "instance_type": settings.test_instance_type,
        "node_count": 1,
        "priority": priority,
        "namespace": settings.e2e_low_namespace if is_low_priority else settings.e2e_high_namespace,
        "queue_name": settings.e2e_low_queue_name if is_low_priority else settings.e2e_high_queue_name,
        "priority_class": settings.e2e_low_priority_class if is_low_priority else settings.e2e_high_priority_class,
        "entrypoint_command": command,
        "distribution_strategy": "ddp",
        "gpu_count": settings.test_gpu_count,
    }


@pytest.fixture
def low_priority_job_config() -> dict[str, Any]:
    """低优先级任务配置"""
    command = [
        "python",
        "-c",
        "import time; print('Low priority job started'); " "[print(f'Step {i}') or time.sleep(1) for i in range(600)]",
    ]
    return _create_job_config("low", "low-priority", command)


@pytest.fixture
def high_priority_job_config() -> dict[str, Any]:
    """高优先级任务配置"""
    command = ["python", "-c", "print('High priority job completed')"]
    return _create_job_config("critical", "high-priority", command)


@pytest.fixture
def checkpoint_enabled_job_config() -> dict[str, Any]:
    """带检查点的任务配置"""
    training_script = """cat > /tmp/train.py << 'SCRIPT'
import os
import time
import torch
import torch.distributed as dist

# 初始化分布式
if 'WORLD_SIZE' in os.environ:
    dist.init_process_group(backend='nccl')
    rank = dist.get_rank()
    print(f'Initialized rank {rank}')
else:
    rank = 0
    print('Non-distributed mode')

# 检查点目录
checkpoint_dir = os.environ.get('CHECKPOINT_DIR', '/tmp/checkpoints')
os.makedirs(checkpoint_dir, exist_ok=True)

# 模拟训练
for epoch in range(100):
    if rank == 0:
        print(f'Training epoch {epoch}')
        checkpoint_path = os.path.join(checkpoint_dir, f'checkpoint_{epoch}.pt')
        torch.save({'epoch': epoch}, checkpoint_path)
        print(f'Saved: {checkpoint_path}')
    time.sleep(10)

if dist.is_initialized():
    dist.destroy_process_group()
SCRIPT
torchrun --nproc_per_node=1 --nnodes=1 --rdzv_backend=c10d --rdzv_endpoint=localhost:29400 /tmp/train.py"""

    config = _create_job_config("medium", "checkpoint", ["bash", "-c", training_script])
    config["checkpoint_config"] = {
        "enabled": True,
        "interval_seconds": 60,
        "s3_path": settings.checkpoint_s3_path or "s3://ai-training-checkpoints-dev/e2e-tests/",
    }
    return config


# =============================================================================
# 资源跟踪和清理
# =============================================================================

_created_resources: list[dict[str, Any]] = []


def track_resource(resource_type: str, resource_id: str) -> None:
    """跟踪创建的资源"""
    _created_resources.append(
        {
            "type": resource_type,
            "id": resource_id,
            "created_at": datetime.now(UTC),
        }
    )


async def cleanup_all_resources(hyperpod_client: Any) -> None:
    """清理所有资源"""
    cleanup_actions = {
        "training_job": hyperpod_client.cancel_training_job,
        "checkpoint": hyperpod_client.delete_checkpoint,
    }

    for resource in _created_resources:
        action = cleanup_actions.get(resource["type"])
        if action:
            try:
                await action(resource["id"])
                print(f"✅ 清理 {resource['type']}: {resource['id']}")
            except Exception as e:
                print(f"⚠️ 清理失败 {resource['type']}: {resource['id']}: {e}")

    _created_resources.clear()


# =============================================================================
# 辅助 Fixtures
# =============================================================================


@pytest.fixture
def e2e_timeout() -> int:
    """E2E 测试超时（秒）"""
    return settings.e2e_timeout


@pytest.fixture
def e2e_settings():
    """E2E 配置对象"""
    return settings
