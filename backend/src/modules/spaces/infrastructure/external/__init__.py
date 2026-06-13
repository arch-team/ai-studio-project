"""Spaces 模块外部服务客户端."""

from .sagemaker_spaces_client import SageMakerSpacesClient, get_sagemaker_spaces_client
from .studio_space_backend import StudioSpaceBackend

__all__ = ["SageMakerSpacesClient", "get_sagemaker_spaces_client", "StudioSpaceBackend"]
