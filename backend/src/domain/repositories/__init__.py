"""Domain Repository Interfaces - Abstract data access contracts.

Repository interfaces define the contract for data persistence
without specifying implementation details. The infrastructure
layer provides concrete implementations.
"""

from .base import IRepository

__all__ = ["IRepository"]
