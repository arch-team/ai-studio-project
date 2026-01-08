"""
AWS CDK Stacks for AI Training Platform.

This module exports all infrastructure stacks following a layered architecture:
- Layer 1 (Foundation): VPC, IAM base roles
- Layer 2 (Data): Aurora MySQL, S3 buckets, FSx for Lustre
- Layer 3 (Compute): HyperPod EKS cluster with add-ons
- Layer 4 (Network): ALB Ingress, TLS termination

Stack dependencies are explicitly managed through CDK's addDependency mechanism.
"""

from .alb_stack import AlbStack
from .database_stack import DatabaseStack
from .fsx_stack import FsxLustreStack
from .hyperpod_stack import HyperPodStack
from .iam_stack import IamStack
from .network_stack import NetworkStack
from .storage_stack import StorageStack

__all__ = [
    "NetworkStack",
    "DatabaseStack",
    "StorageStack",
    "FsxLustreStack",
    "IamStack",
    "HyperPodStack",
    "AlbStack",
]
