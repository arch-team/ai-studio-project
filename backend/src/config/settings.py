"""应用配置设置

使用pydantic-settings管理环境变量和配置
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础配置
    app_name: str = "AI Training Platform"
    app_version: str = "0.1.0"
    env: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")

    # API配置
    api_prefix: str = "/api/v1"
    api_docs_url: str | None = "/docs"
    api_redoc_url: str | None = "/redoc"
    api_openapi_url: str | None = "/openapi.json"

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False

    # 数据库配置
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://ai_platform:dev_password@localhost:5432/ai_training_platform",
        description="PostgreSQL数据库连接URL",
    )
    database_pool_size: int = Field(default=20, description="数据库连接池大小")
    database_max_overflow: int = Field(default=10, description="数据库连接池最大溢出")
    database_echo: bool = Field(default=False, description="是否打印SQL语句")

    # Redis配置
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL",
    )
    redis_max_connections: int = Field(default=50, description="Redis最大连接数")

    # JWT认证配置
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # CORS配置
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="允许的CORS源",
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # TLS/HTTPS配置
    tls_enabled: bool = Field(default=False, description="是否启用TLS")
    tls_cert_path: str | None = Field(default=None, description="TLS证书路径")
    tls_key_path: str | None = Field(default=None, description="TLS密钥路径")
    tls_min_version: str = Field(default="TLSv1.2", description="最小TLS版本")

    # AWS配置
    aws_region: str = Field(default="us-west-2", description="AWS区域")
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # Kubernetes配置
    k8s_namespace: str = Field(default="ai-training-platform", description="K8S命名空间")
    k8s_config_path: str | None = Field(default=None, description="K8S配置文件路径")
    k8s_in_cluster: bool = Field(default=False, description="是否运行在集群内")

    # HyperPod配置
    hyperpod_cluster_name: str | None = Field(default=None, description="HyperPod集群名称")
    hyperpod_training_operator_namespace: str = Field(
        default="hyperpod-training-operator", description="Training Operator命名空间"
    )

    # 存储配置
    s3_bucket: str | None = Field(default=None, description="S3存储桶名称")
    fsx_filesystem_id: str | None = Field(default=None, description="FSx文件系统ID")
    fsx_mount_path: str = Field(default="/fsx", description="FSx挂载路径")
    efs_filesystem_id: str | None = Field(default=None, description="EFS文件系统ID")
    efs_mount_path: str = Field(default="/efs", description="EFS挂载路径")

    # 监控配置
    prometheus_enabled: bool = Field(default=True, description="是否启用Prometheus")
    prometheus_port: int = Field(default=9090, description="Prometheus端口")
    grafana_url: str | None = Field(default=None, description="Grafana URL")

    # 限流配置
    rate_limit_enabled: bool = Field(default=True, description="是否启用限流")
    rate_limit_requests: int = Field(default=100, description="限流请求数")
    rate_limit_period: int = Field(default=60, description="限流时间窗口(秒)")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"日志级别必须是以下之一: {', '.join(valid_levels)}")
        return v_upper

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.env == "development"

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.env == "production"


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 导出配置实例
settings = get_settings()
