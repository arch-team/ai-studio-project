"""Configuration module - Re-exports settings for backward compatibility."""

from src.infrastructure.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
