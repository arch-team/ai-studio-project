"""Shared API schemas."""

from .base import EntitySchema as ManualMappingEntitySchema
from .enhanced_base import AutoMappingEntitySchema
from .entity_schema import EntitySchema

__all__ = [
    # 新的统一基类 (推荐使用，默认启用自动映射)
    "EntitySchema",
    # 旧名称 (向后兼容)
    "AutoMappingEntitySchema",
    "ManualMappingEntitySchema",
]
