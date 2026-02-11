"""
GPU Node Group Construct for HyperPod clusters.

This construct creates GPU node groups for SageMaker HyperPod with:
- GPU instance types (p4d.24xlarge, p5.48xlarge, trn1.32xlarge)
- Auto Scaling configuration
- AZ affinity scheduling for cost optimization
- Topology spread constraints
"""

from dataclasses import dataclass, field

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from constructs import Construct


@dataclass(frozen=True)
class GpuNodeGroupConfig:
    """Configuration for a GPU node group.

    This is an immutable configuration class following the project's
    dataclass pattern for type safety and consistency.

    Attributes:
        name: Node group name
        instance_types: Tuple of GPU instance types
        min_size: Minimum number of nodes
        max_size: Maximum number of nodes
        desired_size: Desired number of nodes
        disk_size: Root volume size in GB
        capacity_type: 容量类型 (ON_DEMAND 或 SPOT)
        labels: Kubernetes labels for the nodes (immutable mapping)
        taints: Kubernetes taints for the nodes (immutable tuple)
    """

    name: str
    instance_types: tuple[str, ...]
    min_size: int = 0
    max_size: int = 10
    desired_size: int = 0
    disk_size: int = 500
    capacity_type: str = "ON_DEMAND"
    labels: dict[str, str] = field(default_factory=dict)
    taints: tuple[dict[str, str], ...] = ()


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
        vpc: ec2.IVpc,
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
            vpc: VPC for subnet resolution
            **kwargs: Additional construct properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._node_group_config = node_group_config
        self._vpc = vpc

        # Create launch template for GPU instances
        self._launch_template = self._create_launch_template(eks_cluster)

        # Create node group
        self._node_group = self._create_node_group(eks_cluster, node_role, subnets)

    def _create_launch_template(self, _eks_cluster: eks.ICluster) -> ec2.LaunchTemplate:
        """Create EC2 launch template for GPU nodes.

        Configures:
        - EBS root volume with GP3 encryption
        - Detailed monitoring
        - IMDSv2 enforcement

        注意: AL2023 EKS 管理节点组使用 nodeadm 自动引导，
        不再需要自定义 user data 或 /etc/eks/bootstrap.sh。
        NVMe、NVIDIA、EFA 配置由 AL2023 AMI 和 EKS 插件自动处理。
        """
        launch_template = ec2.LaunchTemplate(
            self,
            f"LaunchTemplate-{self._node_group_config.name}",
            launch_template_name=f"{self.env_config.resource_prefix}-{self._node_group_config.name}-lt",
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
            "Name",
            f"{self.env_config.resource_prefix}-{self._node_group_config.name}-lt",
        )

        return launch_template

    def _get_ami_type(self, config: GpuNodeGroupConfig) -> str:
        """根据实例类型从配置体系中选择对应的 AMI 类型。

        AMI 类型由 env_config.eks.addon_versions 中的配置决定，
        与 K8s 版本联动:
        - K8s 1.33: AL2023_x86_64_NVIDIA / AL2023_x86_64_NEURON
        - K8s 1.32: AL2_x86_64_GPU / AL2_x86_64_GPU

        根据实例类型前缀判断使用 gpu_ami_type 或 neuron_ami_type:
        - Neuron 实例 (trn1/inf1/inf2) → neuron_ami_type
        - 其他 GPU 实例 → gpu_ami_type

        Returns:
            EKS AMI 类型字符串
        """
        addon_versions = self.env_config.eks.addon_versions
        neuron_prefixes = ("trn1", "inf1", "inf2")
        if any(
            inst.startswith(neuron_prefixes) for inst in config.instance_types
        ):
            return addon_versions.neuron_ami_type
        return addon_versions.gpu_ami_type

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

        # Select subnets from VPC using subnet_type
        subnet_type = getattr(
            subnets, "subnet_type", ec2.SubnetType.PRIVATE_WITH_EGRESS
        )
        selected_subnets = self._vpc.select_subnets(subnet_type=subnet_type)
        subnet_ids = [subnet.subnet_id for subnet in selected_subnets.subnets]

        # Prepare labels with GPU-specific labels
        labels = {
            **config.labels,
            "node.kubernetes.io/instance-type": config.instance_types[0],
            "nvidia.com/gpu": "true",
            f"{self.env_config.resource_prefix}/node-group": config.name,
        }

        # Prepare taints for GPU node isolation
        taints = (
            [
                eks.CfnNodegroup.TaintProperty(
                    key=t.get("key", "nvidia.com/gpu"),
                    value=t.get("value", "true"),
                    effect=t.get("effect", "NO_SCHEDULE"),
                )
                for t in config.taints
            ]
            if config.taints
            else [
                # Default GPU taint to prevent non-GPU workloads
                eks.CfnNodegroup.TaintProperty(
                    key="nvidia.com/gpu",
                    value="true",
                    effect="NO_SCHEDULE",
                )
            ]
        )

        node_group = eks.CfnNodegroup(
            self,
            f"NodeGroup-{config.name}",
            cluster_name=eks_cluster.cluster_name,
            nodegroup_name=f"{self.env_config.resource_prefix}-{config.name}",
            node_role=node_role.role_arn,
            subnets=subnet_ids,
            # Scaling configuration
            scaling_config=eks.CfnNodegroup.ScalingConfigProperty(
                min_size=config.min_size,
                max_size=config.max_size,
                desired_size=config.desired_size,
            ),
            # Instance configuration
            instance_types=list(config.instance_types),
            ami_type=self._get_ami_type(config),  # AL2023 系列，兼容 K8s 1.33+
            capacity_type=config.capacity_type,
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
            # Tags (static keys only - dynamic cluster name tags applied separately)
            tags={
                "Name": f"{self.env_config.resource_prefix}-{config.name}",
                "k8s.io/cluster-autoscaler/enabled": "true",
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


def _default_node_group_definitions(
    max_nodes: int,
) -> list[tuple[str, GpuNodeGroupConfig]]:
    """返回默认 GPU 节点组的 (construct_id, config) 定义列表。"""
    max_per_group = max_nodes // 3
    return [
        # P4d: NVIDIA A100 GPUs (8x 40GB)
        (
            "P4dNodeGroup",
            GpuNodeGroupConfig(
                name="p4d-gpu",
                instance_types=("p4d.24xlarge",),
                max_size=max_per_group,
                disk_size=500,
                labels={
                    "nvidia.com/gpu.product": "NVIDIA-A100-SXM4-40GB",
                    "nvidia.com/gpu.memory": "40960",
                },
            ),
        ),
        # P5: NVIDIA H100 GPUs (8x 80GB)
        (
            "P5NodeGroup",
            GpuNodeGroupConfig(
                name="p5-gpu",
                instance_types=("p5.48xlarge",),
                max_size=max_per_group,
                disk_size=1000,
                labels={
                    "nvidia.com/gpu.product": "NVIDIA-H100-80GB-HBM3",
                    "nvidia.com/gpu.memory": "81920",
                },
            ),
        ),
        # Trn1: AWS Trainium chips
        (
            "Trn1NodeGroup",
            GpuNodeGroupConfig(
                name="trn1-neuron",
                instance_types=("trn1.32xlarge",),
                max_size=max_per_group,
                disk_size=500,
                labels={
                    "aws.amazon.com/neuron": "true",
                    "node.kubernetes.io/instance-type": "trn1.32xlarge",
                },
                taints=(
                    {
                        "key": "aws.amazon.com/neuron",
                        "value": "true",
                        "effect": "NO_SCHEDULE",
                    },
                ),
            ),
        ),
    ]


def create_default_gpu_node_groups(
    scope: Construct,
    env_config: EnvironmentConfig,
    eks_cluster: eks.ICluster,
    node_role: iam.IRole,
    subnets: ec2.SubnetSelection,
    vpc: ec2.IVpc,
) -> list[GpuNodeGroupConstruct]:
    """Create default GPU node groups for the platform.

    Creates node groups for different accelerator types:
    - p4d: NVIDIA A100 GPUs (8x 40GB)
    - p5: NVIDIA H100 GPUs (8x 80GB)
    - trn1: AWS Trainium chips

    Args:
        scope: CDK scope
        env_config: Environment configuration
        eks_cluster: EKS cluster
        node_role: Node IAM role
        subnets: Subnet selection
        vpc: VPC for subnet resolution

    Returns:
        List of created node group constructs
    """
    definitions = _default_node_group_definitions(env_config.eks.max_nodes)
    return [
        GpuNodeGroupConstruct(
            scope,
            construct_id,
            env_config=env_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            node_group_config=config,
            subnets=subnets,
            vpc=vpc,
        )
        for construct_id, config in definitions
    ]
