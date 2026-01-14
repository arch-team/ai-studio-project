"""HyperPod Adapter - SageMaker HyperPod SDK integration.

Implements IHyperPodClient interface using boto3 and sagemaker-hyperpod SDK.
"""

from src.infrastructure.external.hyperpod.client import HyperPodClient

__all__ = ["HyperPodClient"]
