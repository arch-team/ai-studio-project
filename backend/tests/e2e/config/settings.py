"""E2E 测试配置管理 - Pydantic Settings 实现

配置加载优先级：
1. 环境变量（最高优先级）
2. .env.e2e.{environment} 文件
3. 代码默认值（仅用于单元测试 mock）

使用方法：
    from tests.e2e.config import get_e2e_settings
    settings = get_e2e_settings()
    print(settings.aws_region)
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class E2ETestSettings(BaseSettings):
    """E2E 测试配置类 - 集中管理所有环境配置"""

    model_config = SettingsConfigDict(
        env_file=(".env.e2e.dev", ".env.e2e"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========== AWS 基础配置 ==========
    aws_region: str = Field(
        default="us-east-1",
        description="AWS 区域",
    )
    aws_account_id: str = Field(
        default="",
        description="AWS 账号 ID（写测试必填）",
    )

    # ========== HyperPod 配置 ==========
    hyperpod_cluster_name: str = Field(
        default="",
        description="HyperPod 集群名称（写测试必填）",
    )
    hyperpod_eks_cluster_name: str = Field(
        default="",
        description="关联的 EKS 集群名称",
    )

    # ========== ECR 镜像配置 ==========
    test_image_uri: str = Field(
        default="",
        description="测试用 PyTorch 镜像 URI（可使用 {aws_account_id}, {aws_region} 占位符）",
    )
    pytorch_image_tag: str = Field(
        default="2.1.0-gpu-py310-cu121-ubuntu20.04-sagemaker",
        description="PyTorch 镜像标签",
    )

    # ========== Task Governance 配置 ==========
    # 低优先级队列
    e2e_low_namespace: str = Field(default="hyperpod-ns-e2e-low")
    e2e_low_queue_name: str = Field(default="hyperpod-ns-e2e-low-localqueue")
    e2e_low_priority_class: str = Field(default="low-priority")

    # 高优先级队列
    e2e_high_namespace: str = Field(default="hyperpod-ns-e2e-high")
    e2e_high_queue_name: str = Field(default="hyperpod-ns-e2e-high-localqueue")
    e2e_high_priority_class: str = Field(default="high-priority")

    # ========== 实例配置 ==========
    test_instance_type: str = Field(default="ml.g5.2xlarge")
    test_gpu_count: int = Field(default=1)

    # ========== S3 配置 ==========
    checkpoint_s3_bucket: str = Field(default="")
    checkpoint_s3_prefix: str = Field(default="e2e-tests/checkpoints")

    # ========== 测试控制 ==========
    e2e_read_only: bool = Field(
        default=True,
        description="只读模式（跳过写操作测试）",
    )
    e2e_timeout: int = Field(
        default=600,
        description="总体超时（秒）",
    )

    # ========== 测试用户凭证 ==========
    e2e_admin_username: str = Field(default="admin")
    e2e_admin_password: str = Field(
        default="",
        description="管理员密码（必填）",
    )
    e2e_test_username: str = Field(default="e2e_test_user")
    e2e_test_password: str = Field(
        default="",
        description="测试用户密码（必填）",
    )
    e2e_test_email: str = Field(default="e2e_test@example.com")

    # ========== SSO 配置 ==========
    sso_health_endpoint: str = Field(default="/api/v1/auth/sso/health")

    # ========== SLA 常量 ==========
    sla_checkpoint_save_timeout: int = Field(
        default=300,
        description="Checkpoint 保存超时（秒）",
    )
    sla_pod_release_timeout: int = Field(
        default=30,
        description="Pod 释放超时（秒）",
    )
    sla_sso_failover_timeout: int = Field(
        default=5,
        description="SSO 故障转移超时（秒）",
    )
    sla_sso_recovery_check_interval: int = Field(
        default=60,
        description="SSO 健康检查间隔（秒）",
    )
    sla_job_submission_timeout: int = Field(
        default=120,
        description="任务提交超时（秒）",
    )
    sla_job_status_poll_interval: int = Field(
        default=5,
        description="任务状态轮询间隔（秒）",
    )
    sla_max_preemption_count: int = Field(
        default=3,
        description="最大抢占次数",
    )

    # ========== 计算属性 ==========
    @computed_field
    @property
    def resolved_image_uri(self) -> str:
        """解析镜像 URI，替换占位符"""
        if self.test_image_uri:
            return self.test_image_uri.format(
                aws_account_id=self.aws_account_id,
                aws_region=self.aws_region,
            )
        # 使用 AWS 官方 DLC 镜像
        return (
            f"763104351884.dkr.ecr.{self.aws_region}.amazonaws.com/"
            f"pytorch-training:{self.pytorch_image_tag}"
        )

    @computed_field
    @property
    def checkpoint_s3_path(self) -> str:
        """完整的 S3 路径"""
        if not self.checkpoint_s3_bucket:
            return ""
        return f"s3://{self.checkpoint_s3_bucket}/{self.checkpoint_s3_prefix}"

    def validate_for_write_tests(self) -> list[str]:
        """验证写测试必填字段，返回缺失字段列表"""
        missing = []
        if not self.hyperpod_cluster_name:
            missing.append("HYPERPOD_CLUSTER_NAME")
        if not self.aws_account_id:
            missing.append("AWS_ACCOUNT_ID")
        if not self.e2e_admin_password:
            missing.append("E2E_ADMIN_PASSWORD")
        return missing


@lru_cache
def get_e2e_settings() -> E2ETestSettings:
    """获取单例配置实例"""
    return E2ETestSettings()
