"""Application Settings - Pydantic settings configuration.

Loads configuration from environment variables with validation.
"""

from functools import lru_cache
from typing import Optional

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

    # Database
    database_url: str = (
        "mysql+aiomysql://ai_training:ai_training_pass@localhost:3306/ai_training"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # S3
    s3_bucket_name: str = "ai-training-platform"
    s3_prefix: str = "data"

    # HyperPod
    hyperpod_cluster_name: Optional[str] = None

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
