"""
AWS CDK Stacks for AI Training Platform.

This module exports all infrastructure stacks following a layered architecture:
- Layer 1 (Foundation): VPC, IAM base roles
- Layer 2 (Data): Aurora MySQL, S3 buckets
- Layer 3a (Compute Foundation): EKS cluster with add-ons + HyperPod Helm Chart
- Layer 3b (Compute): SageMaker HyperPod cluster
- Layer 4 (Storage): FSx for Lustre
- Layer 5 (Network): ALB Ingress, TLS termination

Stack dependencies are explicitly managed through CDK's addDependency mechanism.

Deployment Order:
1. NetworkStack, IamStack (parallel)
2. DatabaseStack, StorageStack (parallel)
3. EksStack (includes automatic Helm Chart installation)
4. SagemakerHyperPodStack
5. FsxLustreStack
6. AlbStack
"""

from .alb_stack import AlbStack
from .database_stack import DatabaseStack
from .eks_stack import EksStack
from .fsx_stack import FsxLustreStack
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
    "SagemakerHyperPodStack",
    "AlbStack",
]
