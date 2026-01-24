"""AWS E2E 测试共享配置和 Fixture

提供真实 AWS 环境测试所需的:
- Skip 条件装饰器
- SLA 常量定义
- AWS 客户端 Fixture
- 测试任务配置 Fixture
- 资源清理策略
"""

import os
import time
from collections.abc import AsyncGenerator
from datetime import datetime, UTC
from typing import Any

import boto3
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from tests.shared.constants import TEST_API_BASE_URL


# =============================================================================
# Skip 条件装饰器
# =============================================================================


def _check_aws_credentials() -> bool:
    """检查 AWS 凭证是否可用 (支持 SSO/配置文件/环境变量)"""
    try:
        sts = boto3.client("sts")
        sts.get_caller_identity()
        return True
    except Exception:
        return False


def _check_hyperpod_cluster() -> bool:
    """检查 HyperPod 集群是否配置"""
    return bool(os.getenv("HYPERPOD_CLUSTER_NAME"))


def _check_sso_configured() -> bool:
    """检查 SSO IdP 是否配置 (可选，用于 SSO 特定测试)"""
    # SSO 测试不强制要求外部 IdP，可以测试本地降级逻辑
    return True  # 默认允许运行


def _check_task_governance() -> bool:
    """检查 Task Governance 是否配置

    使用 SageMaker API 检查:
    - Cluster Scheduler Config (PriorityClasses)
    - Compute Quotas (Team allocations)

    参考: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance.html
    """
    try:
        cluster_name = os.getenv("HYPERPOD_CLUSTER_NAME")
        if not cluster_name:
            return False

        sagemaker = boto3.client("sagemaker")

        # 获取集群 ARN
        clusters = sagemaker.list_clusters(NameContains=cluster_name)
        if not clusters.get("ClusterSummaries"):
            return False

        cluster_arn = clusters["ClusterSummaries"][0]["ClusterArn"]

        # 检查 Cluster Scheduler Config (PriorityClasses)
        try:
            configs = sagemaker.list_cluster_scheduler_configs(ClusterArn=cluster_arn)
            has_scheduler_config = bool(configs.get("ClusterSchedulerConfigSummaries"))
        except Exception:
            has_scheduler_config = False

        # 检查 Compute Quotas (Team allocations)
        try:
            quotas = sagemaker.list_compute_quotas(ClusterArn=cluster_arn)
            has_compute_quotas = bool(quotas.get("ComputeQuotaSummaries"))
        except Exception:
            has_compute_quotas = False

        return has_scheduler_config and has_compute_quotas
    except Exception:
        return False


# AWS 凭证检查 - 支持 SSO/配置文件/环境变量
skip_without_aws = pytest.mark.skipif(
    not _check_aws_credentials(),
    reason="AWS credentials not configured (SSO/Profile/EnvVar)",
)

skip_without_hyperpod = pytest.mark.skipif(
    not _check_hyperpod_cluster(),
    reason="HyperPod cluster not configured (set HYPERPOD_CLUSTER_NAME)",
)

skip_without_sso = pytest.mark.skipif(
    not _check_sso_configured(),
    reason="SSO IdP not configured",
)

skip_write_tests = pytest.mark.skipif(
    os.getenv("E2E_READ_ONLY", "true").lower() == "true",
    reason="Write tests disabled (E2E_READ_ONLY=true)",
)

skip_without_task_governance = pytest.mark.skipif(
    not _check_task_governance(),
    reason="Task Governance not configured (requires ClusterQueues and WorkloadPriorityClasses)",
)


# =============================================================================
# SLA 常量
# =============================================================================


class SLAConstants:
    """SLA 时间窗口定义 (单位: 秒)"""

    # 抢占相关 SLA
    CHECKPOINT_SAVE_TIMEOUT = 300  # 5 分钟 - checkpoint 保存超时
    POD_RELEASE_TIMEOUT = 30  # 30 秒 - Pod 释放超时

    # SSO 相关 SLA
    SSO_FAILOVER_TIMEOUT = 5  # 5 秒 - IdP 超时阈值
    SSO_RECOVERY_CHECK_INTERVAL = 60  # 健康检查间隔

    # 任务相关超时
    JOB_SUBMISSION_TIMEOUT = 120  # 任务提交超时
    JOB_STATUS_POLL_INTERVAL = 5  # 状态轮询间隔

    # 抢占限制
    MAX_PREEMPTION_COUNT = 3  # 最大抢占次数


# =============================================================================
# AWS 客户端 Fixture
# =============================================================================


@pytest.fixture(scope="session")
def aws_region() -> str:
    """AWS 区域"""
    return os.getenv("AWS_REGION", "us-west-2")


@pytest.fixture(scope="session")
def hyperpod_cluster_name() -> str:
    """HyperPod 集群名称"""
    return os.getenv("HYPERPOD_CLUSTER_NAME", "ai-training-cluster-dev")


@pytest.fixture(scope="session")
def sagemaker_client(aws_region: str):
    """SageMaker 客户端"""
    return boto3.client("sagemaker", region_name=aws_region)


@pytest.fixture(scope="session")
def s3_client(aws_region: str):
    """S3 客户端"""
    return boto3.client("s3", region_name=aws_region)


# =============================================================================
# HyperPod 客户端 Fixture (延迟导入避免启动时报错)
# =============================================================================


@pytest.fixture(scope="function")
def hyperpod_client(
    hyperpod_cluster_name: str,
    aws_region: str,
) -> Any:
    """真实 HyperPod 客户端 (同步初始化)

    延迟导入以避免 AWS 凭证未配置时启动失败
    """
    try:
        from src.modules.training.infrastructure.hyperpod.client import HyperPodClient

        client = HyperPodClient(region=aws_region)
        # 保存集群名称供测试使用
        client._cluster_name = hyperpod_cluster_name
        return client
    except ImportError:
        pytest.skip("HyperPodClient not available")
    except Exception as e:
        pytest.skip(f"HyperPodClient initialization failed: {e}")


# =============================================================================
# HTTP 客户端 Fixture
# =============================================================================


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """异步 HTTP 客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=TEST_API_BASE_URL,
        timeout=60.0,  # E2E 测试使用更长超时
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def admin_token(async_client: AsyncClient) -> str:
    """获取管理员 Token

    在真实环境中需要配置测试管理员账号
    """
    admin_username = os.getenv("E2E_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("E2E_ADMIN_PASSWORD", "admin123")

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_username, "password": admin_password},
    )

    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")

    data = response.json()
    # API 返回嵌套结构: {tokens: {access_token: ...}, user: {...}}
    if "tokens" in data:
        return data["tokens"]["access_token"]
    return data["access_token"]


# =============================================================================
# 测试用户 Fixture
# =============================================================================


@pytest.fixture
def test_local_user() -> dict[str, str]:
    """本地测试用户配置"""
    return {
        "username": os.getenv("E2E_TEST_USERNAME", "e2e_test_user"),
        "password": os.getenv("E2E_TEST_PASSWORD", "test_password_123"),
        "email": os.getenv("E2E_TEST_EMAIL", "e2e_test@example.com"),
    }


@pytest.fixture
def sso_health_endpoint() -> str:
    """SSO 健康检查端点"""
    return os.getenv("SSO_HEALTH_ENDPOINT", "/api/v1/auth/sso/health")


# =============================================================================
# 测试任务配置 Fixture
# =============================================================================


@pytest.fixture
def low_priority_job_config() -> dict[str, Any]:
    """低优先级测试任务配置

    使用 Task Governance 配置:
    - namespace: hyperpod-ns-e2e-low
    - queue: hyperpod-ns-e2e-low-localqueue
    - priority: low-priority

    训练脚本使用简单的 sleep 循环模拟长时间训练。
    """
    return {
        "job_name": f"e2e-low-priority-{int(time.time())}",
        "image_uri": os.getenv(
            "TEST_IMAGE_URI",
            "763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-training:2.1.0-gpu-py310-cu121-ubuntu20.04-sagemaker",
        ),
        "instance_type": os.getenv("TEST_INSTANCE_TYPE", "ml.g5.2xlarge"),
        "node_count": 1,
        "priority": "low",
        # Task Governance 配置
        "namespace": "hyperpod-ns-e2e-low",
        "queue_name": "hyperpod-ns-e2e-low-localqueue",
        "priority_class": "low-priority",
        # 简单的训练命令 - sleep 模拟长时间训练
        "entrypoint_command": ["python", "-c", "import time; print('Low priority job started'); [print(f'Step {i}') or time.sleep(1) for i in range(600)]"],
        "distribution_strategy": "ddp",
        "gpu_count": 1,
    }


@pytest.fixture
def high_priority_job_config() -> dict[str, Any]:
    """高优先级测试任务配置 (用于触发抢占)

    使用 Task Governance 配置:
    - namespace: hyperpod-ns-e2e-high
    - queue: hyperpod-ns-e2e-high-localqueue
    - priority: critical-priority (最高优先级，触发抢占)
    """
    return {
        "job_name": f"e2e-high-priority-{int(time.time())}",
        "image_uri": os.getenv(
            "TEST_IMAGE_URI",
            "763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-training:2.1.0-gpu-py310-cu121-ubuntu20.04-sagemaker",
        ),
        "instance_type": os.getenv("TEST_INSTANCE_TYPE", "ml.g5.2xlarge"),
        "node_count": 1,
        "priority": "critical",
        # Task Governance 配置
        "namespace": "hyperpod-ns-e2e-high",
        "queue_name": "hyperpod-ns-e2e-high-localqueue",
        "priority_class": "high-priority",
        # 简短任务 - 快速完成
        "entrypoint_command": ["python", "-c", "print('High priority job completed')"],
        "distribution_strategy": "ddp",
        "gpu_count": 1,
    }


@pytest.fixture
def checkpoint_enabled_job_config() -> dict[str, Any]:
    """启用 Checkpoint 的测试任务配置

    使用 torchrun 启动训练并定期保存检查点。
    """
    # 训练脚本带检查点保存
    training_command = """cat > /tmp/train.py << 'SCRIPT'
import os
import time
import torch
import torch.distributed as dist

# 初始化分布式环境
if 'WORLD_SIZE' in os.environ:
    dist.init_process_group(backend='nccl')
    rank = dist.get_rank()
    print(f'Initialized rank {rank}')
else:
    rank = 0
    print('Running in non-distributed mode')

# 检查点目录
checkpoint_dir = os.environ.get('CHECKPOINT_DIR', '/tmp/checkpoints')
os.makedirs(checkpoint_dir, exist_ok=True)

# 模拟训练并定期保存状态
for epoch in range(100):
    if rank == 0:
        print(f'Training epoch {epoch}')
        # 创建模拟 checkpoint
        checkpoint_path = os.path.join(checkpoint_dir, f'checkpoint_{epoch}.pt')
        torch.save({'epoch': epoch}, checkpoint_path)
        print(f'Saved checkpoint: {checkpoint_path}')
    time.sleep(10)

if dist.is_initialized():
    dist.destroy_process_group()
SCRIPT
torchrun --nproc_per_node=1 --nnodes=1 --rdzv_backend=c10d --rdzv_endpoint=localhost:29400 /tmp/train.py"""

    return {
        "job_name": f"e2e-checkpoint-{int(time.time())}",
        "image_uri": os.getenv(
            "TEST_IMAGE_URI",
            "763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-training:2.1.0-gpu-py310-cu121-ubuntu20.04-sagemaker",
        ),
        "instance_type": os.getenv("TEST_INSTANCE_TYPE", "ml.g5.2xlarge"),
        "node_count": 1,
        "priority": "medium",
        "entrypoint_command": ["bash", "-c", training_command],
        "distribution_strategy": "ddp",
        "gpu_count": 1,
        "checkpoint_config": {
            "enabled": True,
            "interval_seconds": 60,
            "s3_path": os.getenv(
                "TEST_CHECKPOINT_S3_PATH",
                "s3://ai-training-checkpoints-dev/e2e-tests/",
            ),
        },
    }


# =============================================================================
# 全局资源跟踪和清理
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
    """清理所有创建的资源"""
    for resource in _created_resources:
        try:
            if resource["type"] == "training_job":
                await hyperpod_client.cancel_training_job(resource["id"])
                print(f"✅ 清理 training_job: {resource['id']}")
            elif resource["type"] == "checkpoint":
                await hyperpod_client.delete_checkpoint(resource["id"])
                print(f"✅ 清理 checkpoint: {resource['id']}")
        except Exception as e:
            print(f"⚠️ 清理失败 {resource['type']}: {resource['id']}: {e}")
    _created_resources.clear()


# 注: cleanup_on_exit 已移除 autouse=True
# 资源清理在各测试的 finally 块中处理，避免 pytest-asyncio scope 问题


# =============================================================================
# 辅助 Fixture
# =============================================================================


@pytest.fixture
def e2e_timeout() -> int:
    """E2E 测试总体超时时间 (秒)"""
    return int(os.getenv("E2E_TIMEOUT", "600"))  # 默认 10 分钟
