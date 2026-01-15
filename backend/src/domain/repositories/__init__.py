"""Domain Repository Interfaces - Abstract data access contracts.

Repository interfaces define the contract for data persistence
without specifying implementation details. The infrastructure
layer provides concrete implementations.
"""

from .base import IRepository
from .resource_limit_config_repository import IResourceLimitConfigRepository

__all__ = ["IRepository", "IResourceLimitConfigRepository"]
