"""
Unit tests for GPU Node Group Construct.

Tests cover:
- GpuNodeGroupConfig 配置验证
- GpuNodeGroupConstruct 创建
- Launch Template 配置
- Node Group 各种实例类型组合
- create_default_gpu_node_groups 工厂函数
"""

import aws_cdk as cdk
import pytest
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk.assertions import Match, Template
from aws_cdk.lambda_layer_kubectl_v33 import KubectlV33Layer

from cdk_constructs.gpu_node_group import (
    GpuNodeGroupConfig,
    GpuNodeGroupConstruct,
    create_default_gpu_node_groups,
)
from config import EnvironmentConfig


class TestGpuNodeGroupConfig:
    """Tests for GpuNodeGroupConfig dataclass."""

    def test_default_values(self) -> None:
        """验证默认配置值."""
        config = GpuNodeGroupConfig(
            name="test-gpu",
            instance_types=("p4d.24xlarge",),
        )
        assert config.min_size == 0
        assert config.max_size == 10
        assert config.desired_size == 0
        assert config.disk_size == 500
        assert config.labels == {}
        assert config.taints == ()

    def test_custom_values(self) -> None:
        """验证自定义配置值."""
        config = GpuNodeGroupConfig(
            name="custom-gpu",
            instance_types=("p5.48xlarge",),
            min_size=1,
            max_size=20,
            desired_size=5,
            disk_size=1000,
            labels={"gpu-type": "h100"},
            taints=(
                {"key": "nvidia.com/gpu", "value": "true", "effect": "NO_SCHEDULE"},
            ),
        )
        assert config.name == "custom-gpu"
        assert config.min_size == 1
        assert config.max_size == 20
        assert config.desired_size == 5
        assert config.disk_size == 1000
        assert config.labels == {"gpu-type": "h100"}
        assert len(config.taints) == 1

    def test_frozen_dataclass(self) -> None:
        """验证配置不可变."""
        config = GpuNodeGroupConfig(
            name="test",
            instance_types=("p4d.24xlarge",),
        )
        with pytest.raises(AttributeError):
            config.name = "changed"  # type: ignore[misc]


class TestGpuNodeGroupConstruct:
    """Tests for GpuNodeGroupConstruct."""

    @pytest.fixture
    def stack(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> cdk.Stack:
        """创建测试 Stack."""
        return cdk.Stack(cdk_app, "TestStack", env=cdk_env)

    @pytest.fixture
    def vpc(self, stack: cdk.Stack) -> ec2.Vpc:
        """创建测试 VPC."""
        return ec2.Vpc(stack, "TestVpc", max_azs=2)

    @pytest.fixture
    def eks_cluster(self, stack: cdk.Stack, vpc: ec2.Vpc) -> eks.Cluster:
        """创建测试 EKS 集群."""
        return eks.Cluster(
            stack,
            "TestCluster",
            cluster_name="test-cluster",
            version=eks.KubernetesVersion.of("1.33"),
            vpc=vpc,
            default_capacity=0,
            kubectl_layer=KubectlV33Layer(stack, "KubectlLayer"),
        )

    @pytest.fixture
    def node_role(self, stack: cdk.Stack) -> iam.Role:
        """创建测试节点角色."""
        return iam.Role(
            stack,
            "TestNodeRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )

    def test_creates_node_group(
        self,
        stack: cdk.Stack,
        dev_config: EnvironmentConfig,
        eks_cluster: eks.Cluster,
        node_role: iam.Role,
        vpc: ec2.Vpc,
    ) -> None:
        """验证 GPU NodeGroup 创建."""
        config = GpuNodeGroupConfig(
            name="test-gpu",
            instance_types=("p4d.24xlarge",),
            min_size=0,
            max_size=5,
            desired_size=0,
        )

        construct = GpuNodeGroupConstruct(
            stack,
            "TestGpuNodeGroup",
            env_config=dev_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            node_group_config=config,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc=vpc,
        )

        assert construct.node_group is not None
        assert construct.launch_template is not None

    def test_launch_template_has_imdsv2(
        self,
        stack: cdk.Stack,
        dev_config: EnvironmentConfig,
        eks_cluster: eks.Cluster,
        node_role: iam.Role,
        vpc: ec2.Vpc,
    ) -> None:
        """验证 Launch Template 强制 IMDSv2."""
        config = GpuNodeGroupConfig(
            name="test-gpu",
            instance_types=("p4d.24xlarge",),
        )

        GpuNodeGroupConstruct(
            stack,
            "TestGpuNodeGroup",
            env_config=dev_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            node_group_config=config,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc=vpc,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::EC2::LaunchTemplate",
            {
                "LaunchTemplateData": Match.object_like(
                    {
                        "MetadataOptions": {
                            "HttpTokens": "required",
                        },
                    }
                ),
            },
        )

    def test_launch_template_has_encrypted_ebs(
        self,
        stack: cdk.Stack,
        dev_config: EnvironmentConfig,
        eks_cluster: eks.Cluster,
        node_role: iam.Role,
        vpc: ec2.Vpc,
    ) -> None:
        """验证 Launch Template EBS 卷加密."""
        config = GpuNodeGroupConfig(
            name="test-gpu",
            instance_types=("p4d.24xlarge",),
            disk_size=500,
        )

        GpuNodeGroupConstruct(
            stack,
            "TestGpuNodeGroup",
            env_config=dev_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            node_group_config=config,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc=vpc,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::EC2::LaunchTemplate",
            {
                "LaunchTemplateData": Match.object_like(
                    {
                        "BlockDeviceMappings": Match.array_with(
                            [
                                Match.object_like(
                                    {
                                        "Ebs": Match.object_like(
                                            {
                                                "Encrypted": True,
                                                "VolumeSize": 500,
                                                "VolumeType": "gp3",
                                            }
                                        ),
                                    }
                                ),
                            ]
                        ),
                    }
                ),
            },
        )

    def test_node_group_scaling_config(
        self,
        stack: cdk.Stack,
        dev_config: EnvironmentConfig,
        eks_cluster: eks.Cluster,
        node_role: iam.Role,
        vpc: ec2.Vpc,
    ) -> None:
        """验证 NodeGroup 自动扩展配置."""
        config = GpuNodeGroupConfig(
            name="test-gpu",
            instance_types=("p4d.24xlarge",),
            min_size=0,
            max_size=10,
            desired_size=2,
        )

        GpuNodeGroupConstruct(
            stack,
            "TestGpuNodeGroup",
            env_config=dev_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            node_group_config=config,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc=vpc,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::EKS::Nodegroup",
            {
                "ScalingConfig": {
                    "MinSize": 0,
                    "MaxSize": 10,
                    "DesiredSize": 2,
                },
            },
        )

    def test_node_group_has_gpu_taint(
        self,
        stack: cdk.Stack,
        dev_config: EnvironmentConfig,
        eks_cluster: eks.Cluster,
        node_role: iam.Role,
        vpc: ec2.Vpc,
    ) -> None:
        """验证 NodeGroup 有 GPU taint 隔离."""
        config = GpuNodeGroupConfig(
            name="test-gpu",
            instance_types=("p4d.24xlarge",),
        )

        GpuNodeGroupConstruct(
            stack,
            "TestGpuNodeGroup",
            env_config=dev_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            node_group_config=config,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc=vpc,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::EKS::Nodegroup",
            {
                "Taints": Match.array_with(
                    [
                        {
                            "Key": "nvidia.com/gpu",
                            "Value": "true",
                            "Effect": "NO_SCHEDULE",
                        }
                    ]
                ),
            },
        )


class TestCreateDefaultGpuNodeGroups:
    """Tests for create_default_gpu_node_groups factory function."""

    @pytest.fixture
    def stack(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> cdk.Stack:
        """创建测试 Stack."""
        return cdk.Stack(cdk_app, "TestStack", env=cdk_env)

    @pytest.fixture
    def vpc(self, stack: cdk.Stack) -> ec2.Vpc:
        """创建测试 VPC."""
        return ec2.Vpc(stack, "TestVpc", max_azs=2)

    @pytest.fixture
    def eks_cluster(self, stack: cdk.Stack, vpc: ec2.Vpc) -> eks.Cluster:
        """创建测试 EKS 集群."""
        return eks.Cluster(
            stack,
            "TestCluster",
            cluster_name="test-cluster",
            version=eks.KubernetesVersion.of("1.33"),
            vpc=vpc,
            default_capacity=0,
            kubectl_layer=KubectlV33Layer(stack, "KubectlLayer"),
        )

    @pytest.fixture
    def node_role(self, stack: cdk.Stack) -> iam.Role:
        """创建测试节点角色."""
        return iam.Role(
            stack,
            "TestNodeRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )

    def test_creates_three_node_groups(
        self,
        stack: cdk.Stack,
        dev_config: EnvironmentConfig,
        eks_cluster: eks.Cluster,
        node_role: iam.Role,
        vpc: ec2.Vpc,
    ) -> None:
        """验证创建 3 个默认 GPU NodeGroup (p4d, p5, trn1)."""
        node_groups = create_default_gpu_node_groups(
            scope=stack,
            env_config=dev_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc=vpc,
        )

        assert len(node_groups) == 3

    def test_node_groups_have_correct_instance_types(
        self,
        stack: cdk.Stack,
        dev_config: EnvironmentConfig,
        eks_cluster: eks.Cluster,
        node_role: iam.Role,
        vpc: ec2.Vpc,
    ) -> None:
        """验证 NodeGroup 使用正确的实例类型."""
        node_groups = create_default_gpu_node_groups(
            scope=stack,
            env_config=dev_config,
            eks_cluster=eks_cluster,
            node_role=node_role,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc=vpc,
        )

        template = Template.from_stack(stack)

        # 验证 p4d NodeGroup
        template.has_resource_properties(
            "AWS::EKS::Nodegroup",
            {
                "InstanceTypes": ["p4d.24xlarge"],
            },
        )

        # 验证 p5 NodeGroup
        template.has_resource_properties(
            "AWS::EKS::Nodegroup",
            {
                "InstanceTypes": ["p5.48xlarge"],
            },
        )

        # 验证 trn1 NodeGroup
        template.has_resource_properties(
            "AWS::EKS::Nodegroup",
            {
                "InstanceTypes": ["trn1.32xlarge"],
            },
        )

        assert len(node_groups) == 3
