"""Shared Infrastructure - Database, config, storage, and security utilities."""

from .config import Settings, get_settings
from .database import AsyncSessionLocal, Base, engine, get_db
from .external import CloudWatchLogsClient, ICloudWatchLogsClient, get_cloudwatch_logs_client
from .logging_config import (
    bind_context,
    clear_context,
    configure_logging,
    get_logger,
    unbind_context,
)
from .models import SoftDeleteMixin, TimestampMixin
from .pydantic_repository import PydanticRepository
from .query_builder import QueryBuilder
from .storage import IStorageService, S3StorageClient

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Database
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    # External
    "ICloudWatchLogsClient",
    "CloudWatchLogsClient",
    "get_cloudwatch_logs_client",
    # Logging
    "configure_logging",
    "get_logger",
    "bind_context",
    "clear_context",
    "unbind_context",
    # Models
    "TimestampMixin",
    "SoftDeleteMixin",
    # Query
    "QueryBuilder",
    # Repository
    "PydanticRepository",
    # Storage
    "IStorageService",
    "S3StorageClient",
]
