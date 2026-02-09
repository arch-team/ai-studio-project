"""
AWS CDK Stacks for AI Training Platform.

This module exports all infrastructure stacks following a 6-layer architecture:
- L1 (Foundation): NetworkStack, IamStack
- L2 (Data/Storage): DatabaseStack, StorageStack
- L3 (Compute): EksStack → SagemakerHyperPodStack → HyperPodAddonsStack
- L4 (Observability/Storage): ObservabilityStack, FsxLustreStack
- L5 (Network Ingress): AlbStack
- L6 (Application): ApplicationStack

Stack dependencies are explicitly managed through CDK's addDependency mechanism.
Layer numbering follows app.py as the single source of truth (SSOT).
"""

# Application
from .application.application_stack import ApplicationStack

# Layer 3: Compute
from .compute.eks_stack import EksStack
from .compute.hyperpod_addons_stack import HyperPodAddonsStack
from .compute.sagemaker_hyperpod_stack import SagemakerHyperPodStack

# Layer 2: Data + Layer 1: Foundation
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
    "ApplicationStack",
    "AlbStack",
]
