"""E2E 测试配置管理

配置加载优先级：
1. 环境变量（最高优先级）
2. .env.e2e.{environment} 文件
3. 代码默认值
"""

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class E2ETestSettings(BaseSettings):
    """E2E 测试配置"""

    model_config = SettingsConfigDict(
        env_file=(".env.e2e.dev", ".env.e2e"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS 配置
    aws_region: str = Field(default="us-east-1")
    aws_account_id: str = Field(default="")

    # HyperPod 配置
    hyperpod_cluster_name: str = Field(default="")
    hyperpod_eks_cluster_name: str = Field(default="")

    # 镜像配置
    test_image_uri: str = Field(default="")
    pytorch_image_tag: str = Field(default="2.1.0-gpu-py310-cu121-ubuntu20.04-sagemaker")

    # Task Governance - 低优先级
    e2e_low_namespace: str = Field(default="hyperpod-ns-e2e-low")
    e2e_low_queue_name: str = Field(default="hyperpod-ns-e2e-low-localqueue")
    e2e_low_priority_class: str = Field(default="low-priority")

    # Task Governance - 高优先级
    e2e_high_namespace: str = Field(default="hyperpod-ns-e2e-high")
    e2e_high_queue_name: str = Field(default="hyperpod-ns-e2e-high-localqueue")
    e2e_high_priority_class: str = Field(default="high-priority")

    # 实例配置
    test_instance_type: str = Field(default="ml.g5.2xlarge")
    test_gpu_count: int = Field(default=1)

    # S3 配置
    checkpoint_s3_bucket: str = Field(default="")
    checkpoint_s3_prefix: str = Field(default="e2e-tests/checkpoints")

    # 测试控制
    e2e_read_only: bool = Field(default=True)
    e2e_timeout: int = Field(default=600)

    # 用户凭证
    e2e_admin_username: str = Field(default="admin")
    e2e_admin_password: str = Field(default="")
    e2e_test_username: str = Field(default="e2e_test_user")
    e2e_test_password: str = Field(default="")
    e2e_test_email: str = Field(default="e2e_test@example.com")

    # SSO 配置
    sso_health_endpoint: str = Field(default="/api/v1/auth/sso/health")

    # SLA 超时配置（秒）
    sla_checkpoint_save_timeout: int = Field(default=300)
    sla_pod_release_timeout: int = Field(default=30)
    sla_sso_failover_timeout: int = Field(default=5)
    sla_sso_recovery_check_interval: int = Field(default=60)
    sla_job_submission_timeout: int = Field(default=120)
    sla_job_status_poll_interval: int = Field(default=5)
    sla_max_preemption_count: int = Field(default=3)

    @computed_field
    @property
    def resolved_image_uri(self) -> str:
        """解析镜像 URI"""
        if self.test_image_uri:
            return self.test_image_uri.format(
                aws_account_id=self.aws_account_id,
                aws_region=self.aws_region,
            )
        # AWS 官方 DLC 镜像
        return f"763104351884.dkr.ecr.{self.aws_region}.amazonaws.com/pytorch-training:{self.pytorch_image_tag}"

    @computed_field
    @property
    def checkpoint_s3_path(self) -> str:
        """S3 路径"""
        return f"s3://{self.checkpoint_s3_bucket}/{self.checkpoint_s3_prefix}" if self.checkpoint_s3_bucket else ""

    def validate_for_write_tests(self) -> list[str]:
        """验证写测试必填字段"""
        required_fields = {
            "HYPERPOD_CLUSTER_NAME": self.hyperpod_cluster_name,
            "AWS_ACCOUNT_ID": self.aws_account_id,
            "E2E_ADMIN_PASSWORD": self.e2e_admin_password,
        }
        return [name for name, value in required_fields.items() if not value]


@lru_cache
def get_e2e_settings() -> E2ETestSettings:
    """获取配置单例"""
    return E2ETestSettings()
