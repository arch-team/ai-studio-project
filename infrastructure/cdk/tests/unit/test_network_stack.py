"""
Network Stack 单元测试.

测试覆盖:
- VPC 创建与 CIDR 配置
- 3 层子网架构 (public, private-app, private-data)
- 各环境 NAT Gateway 数量
- VPC Endpoints
- VPC Flow Logs
- Stack 输出属性
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import NetworkStack


# 模块级 fixture: 所有测试类共用
@pytest.fixture
def network_stack(
    cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
) -> NetworkStack:
    """创建 Network Stack."""
    return NetworkStack(cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env)


@pytest.fixture
def template(network_stack: NetworkStack) -> Template:
    """获取 CloudFormation 模板."""
    return Template.from_stack(network_stack)


class TestNetworkStackCreation:
    """Network Stack 创建测试."""

    def test_stack_synthesizes(self, network_stack: NetworkStack) -> None:
        """验证 Stack 可以成功合成."""
        assert network_stack is not None

    def test_vpc_created(self, template: Template) -> None:
        """验证 VPC 创建."""
        template.resource_count_is("AWS::EC2::VPC", 1)

    def test_vpc_cidr(self, template: Template) -> None:
        """验证 VPC CIDR 和 DNS 配置."""
        template.has_resource_properties(
            "AWS::EC2::VPC",
            {
                "CidrBlock": "10.0.0.0/16",
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True,
            },
        )


class TestSubnetArchitecture:
    """3 层子网架构测试."""

    def test_public_subnets_created(self, template: Template) -> None:
        """验证公有子网创建."""
        template.has_resource_properties(
            "AWS::EC2::Subnet",
            {
                "MapPublicIpOnLaunch": True,
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {"Key": "aws-cdk:subnet-type", "Value": "Public"}
                        )
                    ]
                ),
            },
        )

    def test_private_subnets_created(self, template: Template) -> None:
        """验证私有子网创建."""
        template.has_resource_properties(
            "AWS::EC2::Subnet",
            {
                "MapPublicIpOnLaunch": False,
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {"Key": "aws-cdk:subnet-type", "Value": "Private"}
                        )
                    ]
                ),
            },
        )

    def test_isolated_subnets_created(self, template: Template) -> None:
        """验证隔离子网 (private-data) 创建."""
        template.has_resource_properties(
            "AWS::EC2::Subnet",
            {
                "MapPublicIpOnLaunch": False,
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {"Key": "aws-cdk:subnet-type", "Value": "Isolated"}
                        )
                    ]
                ),
            },
        )


class TestNatGatewayConfiguration:
    """各环境 NAT Gateway 数量测试."""

    def test_dev_single_nat(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """验证开发环境使用单 NAT Gateway (节省成本)."""
        stack = NetworkStack(cdk_app, "DevNatStack", env_config=dev_config, env=cdk_env)
        Template.from_stack(stack).resource_count_is("AWS::EC2::NatGateway", 1)

    def test_staging_multi_nat(
        self,
        cdk_app: cdk.App,
        staging_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
    ) -> None:
        """验证预发布环境使用多 NAT Gateway (高可用)."""
        stack = NetworkStack(
            cdk_app, "StagingNatStack", env_config=staging_config, env=cdk_env
        )
        Template.from_stack(stack).resource_count_is("AWS::EC2::NatGateway", 2)

    def test_prod_multi_nat(
        self, cdk_app: cdk.App, prod_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """验证生产环境使用多 NAT Gateway."""
        stack = NetworkStack(
            cdk_app, "ProdNatStack", env_config=prod_config, env=cdk_env
        )
        Template.from_stack(stack).resource_count_is("AWS::EC2::NatGateway", 2)


class TestVpcEndpoints:
    """VPC Endpoints 测试."""

    def test_s3_gateway_endpoint(self, template: Template) -> None:
        """验证 S3 Gateway Endpoint 创建."""
        template.has_resource_properties(
            "AWS::EC2::VPCEndpoint",
            {"VpcEndpointType": "Gateway"},
        )

    def test_ecr_interface_endpoints(self, template: Template) -> None:
        """验证 ECR Interface Endpoint 创建."""
        template.has_resource_properties(
            "AWS::EC2::VPCEndpoint",
            {"VpcEndpointType": "Interface", "PrivateDnsEnabled": True},
        )


class TestVpcFlowLogs:
    """VPC Flow Logs 测试."""

    def test_flow_logs_enabled(self, template: Template) -> None:
        """验证 VPC Flow Logs 已启用."""
        template.has_resource_properties(
            "AWS::EC2::FlowLog",
            {"ResourceType": "VPC", "TrafficType": "ALL"},
        )


class TestNetworkStackOutputs:
    """Network Stack 输出属性测试."""

    def test_vpc_exported(self, network_stack: NetworkStack) -> None:
        """验证 VPC 可访问."""
        assert network_stack.vpc is not None

    def test_public_subnets_accessible(self, network_stack: NetworkStack) -> None:
        """验证公有子网可访问."""
        assert network_stack.public_subnets is not None

    def test_private_app_subnets_accessible(self, network_stack: NetworkStack) -> None:
        """验证私有应用子网可访问."""
        assert network_stack.private_app_subnets is not None

    def test_private_data_subnets_accessible(self, network_stack: NetworkStack) -> None:
        """验证私有数据子网可访问."""
        assert network_stack.private_data_subnets is not None
