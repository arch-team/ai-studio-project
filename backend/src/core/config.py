"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AI Training Platform"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/ai_training"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_profile: Optional[str] = None

    # HyperPod Configuration
    hyperpod_cluster_arn: Optional[str] = None
    hyperpod_cluster_name: Optional[str] = None

    # Storage
    s3_datasets_bucket: Optional[str] = None
    s3_models_bucket: Optional[str] = None
    s3_checkpoints_bucket: Optional[str] = None
    fsx_lustre_mount_path: str = "/fsx"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 30

    # IAM Identity Center (SSO) Configuration
    sso_enabled: bool = False
    sso_issuer_url: Optional[str] = None  # IAM Identity Center issuer URL
    sso_client_id: Optional[str] = None  # OIDC client ID
    sso_client_secret: Optional[str] = None  # OIDC client secret
    sso_redirect_uri: Optional[str] = None  # OAuth callback URL

    # Local Authentication (fallback when SSO is disabled)
    local_auth_enabled: bool = True
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    login_max_attempts: int = 5
    login_lockout_minutes: int = 30
    password_expire_days: int = 90
    password_history_count: int = 5

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
