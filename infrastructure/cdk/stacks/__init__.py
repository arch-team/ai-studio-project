"""
AWS CDK Stacks for AI Training Platform.

This module exports all infrastructure stacks following a layered architecture:
- Layer 1 (Foundation): VPC, IAM base roles
- Layer 2 (Data): Aurora MySQL
- Layer 3a (Compute Foundation): EKS cluster with add-ons + HyperPod Helm Chart
- Layer 3b (Compute): SageMaker HyperPod cluster
- Layer 3c (HyperPod Add-ons): Training Operator, Task Governance (Kueue), PriorityClass
- Layer 4a (Storage): S3 buckets
- Layer 4b (Storage): FSx for Lustre
- Layer 5 (Network): ALB Ingress, TLS termination

Stack dependencies are explicitly managed through CDK's addDependency mechanism.

Deployment Order:
1. NetworkStack, IamStack (parallel)
2. DatabaseStack, StorageStack (parallel)
3. EksStack (includes automatic Helm Chart installation)
4. SagemakerHyperPodStack
5. HyperPodAddonsStack (Training Operator, Task Governance, PriorityClass)
6. FsxLustreStack
7. AlbStack
"""

# Layer 1: Foundation
# Layer 3: Compute
from .compute.eks_stack import EksStack
from .compute.hyperpod_addons_stack import HyperPodAddonsStack
from .compute.sagemaker_hyperpod_stack import SagemakerHyperPodStack

# Layer 2: Data
from .data.database_stack import DatabaseStack
from .foundation.iam_stack import IamStack
from .foundation.network_stack import NetworkStack

# Layer 5: Networking
from .networking.alb_stack import AlbStack

# Observability
from .observability.observability_stack import ObservabilityStack

# Layer 4: Storage
from .storage.fsx_stack import FsxLustreStack
from .storage.storage_stack import StorageStack

__all__ = [
    "NetworkStack",
    "IamStack",
    "DatabaseStack",
    "StorageStack",
    "FsxLustreStack",
    "EksStack",
    "SagemakerHyperPodStack",
    "HyperPodAddonsStack",
    "ObservabilityStack",
    "AlbStack",
]
