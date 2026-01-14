"""Application Interfaces - Port definitions for external services.

These interfaces define contracts for infrastructure adapters (Ports and Adapters):
- IHyperPodClient: SageMaker HyperPod operations
- IStorageService: S3/FSx storage operations
- IKueueClient: Kubernetes Kueue queue operations
"""

from .hyperpod_client import IHyperPodClient
from .storage_service import IStorageService

__all__ = ["IHyperPodClient", "IStorageService"]
