"""GPU 节点组 Construct — HyperPod 训练加速器管理。

支持 P4d/P5/Trn1 实例，含自动伸缩、AZ 亲和调度、拓扑分布约束。
"""

from dataclasses import dataclass, field
from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam

from config import EnvironmentConfig
from constructs import Construct


@dataclass(frozen=True)
class GpuNodeGroupConfig:
    """GPU 节点组配置。"""

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
    """GPU 节点组 Construct — GPU AMI、EFA、拓扑感知调度。"""

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
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._node_group_config = node_group_config
        self._vpc = vpc

        self._launch_template = self._create_launch_template(eks_cluster)
        self._node_group = self._create_node_group(eks_cluster, node_role, subnets)

    def _create_launch_template(self, _eks_cluster: eks.ICluster) -> ec2.LaunchTemplate:
        """创建 GPU 节点 Launch Template (GP3 加密卷, IMDSv2)。

        AL2023 使用 nodeadm 自动引导，NVMe/NVIDIA/EFA 由 AMI + EKS 插件处理。
        """
        launch_template = ec2.LaunchTemplate(
            self,
            f"LaunchTemplate-{self._node_group_config.name}",
            launch_template_name=f"{self.env_config.resource_prefix}-{self._node_group_config.name}-lt",
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
            detailed_monitoring=True,
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
        if any(inst.startswith(neuron_prefixes) for inst in config.instance_types):
            return addon_versions.neuron_ami_type
        return addon_versions.gpu_ami_type

    def _create_node_group(
        self,
        eks_cluster: eks.ICluster,
        node_role: iam.IRole,
        subnets: ec2.SubnetSelection,
    ) -> eks.CfnNodegroup:
        """创建 GPU 节点组 (使用 L1 CfnNodegroup 以获取更多配置控制)。"""
        config = self._node_group_config

        subnet_type = getattr(
            subnets, "subnet_type", ec2.SubnetType.PRIVATE_WITH_EGRESS
        )
        selected_subnets = self._vpc.select_subnets(subnet_type=subnet_type)
        subnet_ids = [subnet.subnet_id for subnet in selected_subnets.subnets]

        labels = {
            **config.labels,
            "node.kubernetes.io/instance-type": config.instance_types[0],
            "nvidia.com/gpu": "true",
            f"{self.env_config.resource_prefix}/node-group": config.name,
        }

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
                # 默认 GPU taint 防止非 GPU 工作负载调度到此节点
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
            scaling_config=eks.CfnNodegroup.ScalingConfigProperty(
                min_size=config.min_size,
                max_size=config.max_size,
                desired_size=config.desired_size,
            ),
            instance_types=list(config.instance_types),
            ami_type=self._get_ami_type(config),  # AL2023 系列，兼容 K8s 1.33+
            capacity_type=config.capacity_type,
            launch_template=eks.CfnNodegroup.LaunchTemplateSpecificationProperty(
                id=self._launch_template.launch_template_id,
                version=self._launch_template.latest_version_number,
            ),
            labels=labels,
            taints=taints,
            update_config=eks.CfnNodegroup.UpdateConfigProperty(
                max_unavailable=1,
            ),
            tags={
                "Name": f"{self.env_config.resource_prefix}-{config.name}",
                "k8s.io/cluster-autoscaler/enabled": "true",
            },
        )

        return node_group

    @property
    def node_group(self) -> eks.CfnNodegroup:
        return self._node_group

    @property
    def launch_template(self) -> ec2.LaunchTemplate:
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
    """创建默认 GPU 节点组 (P4d A100 / P5 H100 / Trn1)。"""
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
