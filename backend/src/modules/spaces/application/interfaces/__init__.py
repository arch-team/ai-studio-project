"""Spaces 模块应用层接口定义."""

from .sagemaker_spaces_client import ISageMakerSpacesClient
from .space_backend_client import ISpaceBackendClient

__all__ = [
    "ISageMakerSpacesClient",
    "ISpaceBackendClient",
]
