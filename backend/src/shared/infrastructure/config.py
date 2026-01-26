"""Application Settings - Pydantic settings configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Training Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "mysql+aiomysql://ai_training:ai_training_pass@localhost:3306/ai_training"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # S3
    s3_bucket_name: str = "ai-training-platform"
    s3_prefix: str = "data"

    # HyperPod
    hyperpod_cluster_name: str | None = None

    # FSx for Lustre
    fsx_filesystem_id: str = "fs-placeholder"
    fsx_mount_path: str = "/fsx"

    # MLflow (T037a)
    mlflow_tracking_uri: str = "http://mlflow.kubeflow.svc.cluster.local:5000"
    mlflow_experiment_prefix: str = "ai-training-platform"
    mlflow_request_timeout: int = 30  # 秒
    mlflow_max_retries: int = 3

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
