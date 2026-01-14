"""Configuration Management - Application settings.

Centralized configuration using pydantic-settings:
- Database connection settings
- AWS credentials and region
- Feature flags and application settings
"""

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
