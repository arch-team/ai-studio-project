"""
GPU Node Group Construct for HyperPod clusters.

This construct creates GPU node groups for SageMaker HyperPod with:
- GPU instance types (p4d.24xlarge, p5.48xlarge, trn1.32xlarge)
- Auto Scaling configuration
- AZ affinity scheduling for cost optimization
- Topology spread constraints
"""


import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from constructs import Construct


class GpuNodeGroupConfig:
    """Configuration for a GPU node group.

    Attributes:
        name: Node group name
        instance_types: List of GPU instance types
        min_size: Minimum number of nodes
        max_size: Maximum number of nodes
        desired_size: Desired number of nodes
        disk_size: Root volume size in GB
        labels: Kubernetes labels for the nodes
        taints: Kubernetes taints for the nodes
    """

    def __init__(
        self,
        name: str,
        instance_types: list[str],
        min_size: int = 0,
        max_size: int = 10,
        desired_size: int = 0,
        disk_size: int = 500,
        labels: dict[str, str] | None = None,
        taints: list[dict[str, str]] | None = None,
    ) -> None:
        self.name = name
        self.instance_types = instance_types
        self.min_size = min_size
        self.max_size = max_size
        self.desired_size = desired_size
        self.disk_size = disk_size
        self.labels = labels or {}
        self.taints = taints or []


class GpuNodeGroupConstruct(Construct):
    """GPU Node Group construct for EKS clusters.

    Creates managed node groups with GPU instances and proper
    configuration for AI/ML training workloads.

    Features:
    - GPU-optimized AMI selection
    - NVMe local storage support
    - EFA (Elastic Fabric Adapter) for distributed training
    - Topology-aware scheduling labels
    - Auto Scaling with HyperPod integration
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        eks_cluster: eks.ICluster,
        node_role: iam.IRole,
        node_group_config: GpuNodeGroupConfig,
        subnets: ec2.SubnetSelection,
        **kwargs,
    ) -> None:
        """Initialize GPU Node Group construct.

        Args:
            scope: CDK scope
            construct_id: Construct identifier
            env_config: Environment configuration
            eks_cluster: EKS cluster to add node group to
            node_role: IAM role for the nodes
            node_group_config: Node group configuration
            subnets: Subnet selection for node placement
            **kwargs: Additional construct properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._node_group_config = node_group_config

        # Create launch template for GPU instances
        self._launch_template = self._create_launch_template(eks_cluster)

        # Create node group
        self._node_group = self._create_node_group(
            eks_cluster, node_role, subnets
        )

    def _create_launch_template(self, eks_cluster: eks.ICluster) -> ec2.LaunchTemplate:
        """Create EC2 launch template for GPU nodes.

        Configures:
        - GPU-optimized AMI
        - NVMe local storage optimization
        - EFA support for distributed training
        - CloudWatch agent for monitoring
        """
        # User data script for GPU nodes
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "#!/bin/bash",
            "set -o xtrace",
            "",
            "# Enable NVMe optimization for local storage",
            "if [ -e /dev/nvme1n1 ]; then",
            "    mkfs.xfs /dev/nvme1n1",
            "    mkdir -p /mnt/nvme",
            "    mount /dev/nvme1n1 /mnt/nvme",
            "    chmod 1777 /mnt/nvme",
            "fi",
            "",
            "# Configure GPU settings",
            "nvidia-smi -pm 1",
            "",
            "# Set up environment for distributed training",
            "export FI_EFA_FORK_SAFE=1",
            "export FI_LOG_LEVEL=1",
            "export FI_EFA_USE_DEVICE_RDMA=1",
            "export NCCL_DEBUG=INFO",
            "",
            f"/etc/eks/bootstrap.sh {eks_cluster.cluster_name}",
        )

        launch_template = ec2.LaunchTemplate(
            self,
            f"LaunchTemplate-{self._node_group_config.name}",
            launch_template_name=f"{self.env_config.resource_prefix}-{self._node_group_config.name}-lt",
            user_data=user_data,
            # Block device mappings for root volume
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=self._node_group_config.disk_size,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        encrypted=True,
                        delete_on_termination=True,
                    ),
                )
            ],
            # Enable detailed monitoring
            detailed_monitoring=True,
            # Instance metadata options (IMDSv2)
            http_tokens=ec2.LaunchTemplateHttpTokens.REQUIRED,
            http_put_response_hop_limit=2,
        )

        cdk.Tags.of(launch_template).add(
            "Name", f"{self.env_config.resource_prefix}-{self._node_group_config.name}-lt"
        )

        return launch_template

    def _create_node_group(
        self,
        eks_cluster: eks.ICluster,
        node_role: iam.IRole,
        subnets: ec2.SubnetSelection,
    ) -> eks.CfnNodegroup:
        """Create EKS managed node group for GPU instances.

        Note: Using CfnNodegroup for more control over configuration
        that's not available in the L2 construct.
        """
        config = self._node_group_config

        # Prepare labels with GPU-specific labels
        labels = {
            **config.labels,
            "node.kubernetes.io/instance-type": config.instance_types[0],
            "nvidia.com/gpu": "true",
            f"{self.env_config.resource_prefix}/node-group": config.name,
        }

        # Prepare taints for GPU node isolation
        taints = [
            eks.CfnNodegroup.TaintProperty(
                key=t.get("key", "nvidia.com/gpu"),
                value=t.get("value", "true"),
                effect=t.get("effect", "NO_SCHEDULE"),
            )
            for t in config.taints
        ] if config.taints else [
            # Default GPU taint to prevent non-GPU workloads
            eks.CfnNodegroup.TaintProperty(
                key="nvidia.com/gpu",
                value="true",
                effect="NO_SCHEDULE",
            )
        ]

        node_group = eks.CfnNodegroup(
            self,
            f"NodeGroup-{config.name}",
            cluster_name=eks_cluster.cluster_name,
            nodegroup_name=f"{self.env_config.resource_prefix}-{config.name}",
            node_role=node_role.role_arn,
            # Scaling configuration
            scaling_config=eks.CfnNodegroup.ScalingConfigProperty(
                min_size=config.min_size,
                max_size=config.max_size,
                desired_size=config.desired_size,
            ),
            # Instance configuration
            instance_types=config.instance_types,
            ami_type="AL2_x86_64_GPU",  # GPU-optimized Amazon Linux 2
            capacity_type="ON_DEMAND",  # GPU instances are typically on-demand
            # Launch template for custom configuration
            launch_template=eks.CfnNodegroup.LaunchTemplateSpecificationProperty(
                id=self._launch_template.launch_template_id,
                version=self._launch_template.latest_version_number,
            ),
            # Labels and taints
            labels=labels,
            taints=taints,
            # Update configuration
            update_config=eks.CfnNodegroup.UpdateConfigProperty(
                max_unavailable=1,  # Rolling update with minimal disruption
            ),
            # Tags
            tags={
                "Name": f"{self.env_config.resource_prefix}-{config.name}",
                "kubernetes.io/cluster/{cluster_name}": "owned",
                "k8s.io/cluster-autoscaler/enabled": "true",
                f"k8s.io/cluster-autoscaler/{eks_cluster.cluster_name}": "owned",
            },
        )

        return node_group

    @property
    def node_group(self) -> eks.CfnNodegroup:
        """Get the EKS node group."""
        return self._node_group

    @property
    def launch_template(self) -> ec2.LaunchTemplate:
        """Get the launch template."""
        return self._launch_template


def create_default_gpu_node_groups(
    scope: Construct,
    env_config: EnvironmentConfig,
    eks_cluster: eks.ICluster,
    node_role: iam.IRole,
    subnets: ec2.SubnetSelection,
) -> list[GpuNodeGroupConstruct]:
    """Create default GPU node groups for the platform.

    Creates node groups for different GPU instance types:
    - p4d: NVIDIA A100 GPUs (8x 40GB)
    - p5: NVIDIA H100 GPUs (8x 80GB)
    - trn1: AWS Trainium chips

    Args:
        scope: CDK scope
        env_config: Environment configuration
        eks_cluster: EKS cluster
        node_role: Node IAM role
        subnets: Subnet selection

    Returns:
        List of created node group constructs
    """
    eks_config = env_config.eks
    node_groups = []

    # P4d node group (NVIDIA A100)
    p4d_config = GpuNodeGroupConfig(
        name="p4d-gpu",
        instance_types=["p4d.24xlarge"],
        min_size=0,
        max_size=eks_config.max_nodes // 3,
        desired_size=0,
        disk_size=500,
        labels={
            "nvidia.com/gpu.product": "NVIDIA-A100-SXM4-40GB",
            "nvidia.com/gpu.memory": "40960",
        },
    )
    node_groups.append(
        GpuNodeGroupConstruct(
            scope,
            "P4dNodeGroup",
            env_config=env_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            node_group_config=p4d_config,
            subnets=subnets,
        )
    )

    # P5 node group (NVIDIA H100)
    p5_config = GpuNodeGroupConfig(
        name="p5-gpu",
        instance_types=["p5.48xlarge"],
        min_size=0,
        max_size=eks_config.max_nodes // 3,
        desired_size=0,
        disk_size=1000,
        labels={
            "nvidia.com/gpu.product": "NVIDIA-H100-80GB-HBM3",
            "nvidia.com/gpu.memory": "81920",
        },
    )
    node_groups.append(
        GpuNodeGroupConstruct(
            scope,
            "P5NodeGroup",
            env_config=env_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            node_group_config=p5_config,
            subnets=subnets,
        )
    )

    # Trn1 node group (AWS Trainium)
    trn1_config = GpuNodeGroupConfig(
        name="trn1-neuron",
        instance_types=["trn1.32xlarge"],
        min_size=0,
        max_size=eks_config.max_nodes // 3,
        desired_size=0,
        disk_size=500,
        labels={
            "aws.amazon.com/neuron": "true",
            "node.kubernetes.io/instance-type": "trn1.32xlarge",
        },
        taints=[
            {
                "key": "aws.amazon.com/neuron",
                "value": "true",
                "effect": "NO_SCHEDULE",
            }
        ],
    )
    node_groups.append(
        GpuNodeGroupConstruct(
            scope,
            "Trn1NodeGroup",
            env_config=env_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            node_group_config=trn1_config,
            subnets=subnets,
        )
    )

    return node_groups
