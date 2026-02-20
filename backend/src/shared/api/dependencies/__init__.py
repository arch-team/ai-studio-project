"""Shared API Dependencies - 可复用的 FastAPI 依赖注入工具。"""

from .ownership import OwnedResource, check_resource_ownership

__all__ = [
    "OwnedResource",
    "check_resource_ownership",
]
