"""
Reusable CDK Constructs for AI Training Platform.

This module provides L2/L3 constructs that encapsulate best practices:
- Security: Encryption at rest, least privilege IAM
- Networking: VPC endpoint integration, security groups
- Monitoring: CloudWatch integration, alarm patterns
- Cost optimization: Tagging, resource policies

Constructs follow AWS Well-Architected Framework principles.
"""

from .gpu_node_group import (
    GpuNodeGroupConfig,
    GpuNodeGroupConstruct,
    create_default_gpu_node_groups,
)

__all__ = [
    "GpuNodeGroupConfig",
    "GpuNodeGroupConstruct",
    "create_default_gpu_node_groups",
]
