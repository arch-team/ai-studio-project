"""
AWS CDK Stacks for AI Training Platform.

This module exports all infrastructure stacks following a layered architecture:
- Layer 1 (Foundation): VPC, IAM base roles
- Layer 2 (Data): Aurora MySQL, S3 buckets, FSx for Lustre
- Layer 3a (Compute Foundation): EKS cluster with add-ons
- Layer 3b (Compute): SageMaker HyperPod (requires Helm Chart installation after EKS)
- Layer 4 (Network): ALB Ingress, TLS termination

Stack dependencies are explicitly managed through CDK's addDependency mechanism.

Note: HyperPod deployment requires two phases:
1. Deploy EksStack
2. Install HyperPod Helm Chart dependencies on EKS
3. Deploy SagemakerHyperPodStack
"""

from .alb_stack import AlbStack
from .database_stack import DatabaseStack
from .eks_stack import EksStack
from .fsx_stack import FsxLustreStack
from .hyperpod_stack import HyperPodStack
from .iam_stack import IamStack
from .network_stack import NetworkStack
from .sagemaker_hyperpod_stack import SagemakerHyperPodStack
from .storage_stack import StorageStack

__all__ = [
    "NetworkStack",
    "DatabaseStack",
    "StorageStack",
    "FsxLustreStack",
    "IamStack",
    "EksStack",
    "HyperPodStack",  # Legacy - combined EKS + HyperPod
    "SagemakerHyperPodStack",  # New - HyperPod only (requires EksStack + Helm)
    "AlbStack",
]
