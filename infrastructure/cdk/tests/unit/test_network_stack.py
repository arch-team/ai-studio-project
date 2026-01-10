"""
Unit tests for Network Stack.

Tests cover:
- VPC creation with correct CIDR
- 3-tier subnet architecture (public, private-app, private-data)
- NAT Gateway configuration per environment
- VPC Endpoints for AWS services
- VPC Flow Logs enablement
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import NetworkStack


class TestNetworkStackCreation:
    """Tests for Network Stack creation."""

    @pytest.fixture
    def network_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> NetworkStack:
        """Create a Network Stack for testing."""
        return NetworkStack(
            cdk_app,
            "TestNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, network_stack: NetworkStack) -> Template:
        """Get CloudFormation template from the stack."""
        return Template.from_stack(network_stack)

    def test_stack_synthesizes(self, network_stack: NetworkStack) -> None:
        """Verify the stack synthesizes without errors."""
        assert network_stack is not None

    def test_vpc_created(self, template: Template) -> None:
        """Verify VPC is created."""
        template.resource_count_is("AWS::EC2::VPC", 1)

    def test_vpc_cidr(self, template: Template) -> None:
        """Verify VPC uses the correct CIDR block."""
        template.has_resource_properties(
            "AWS::EC2::VPC",
            {
                "CidrBlock": "10.0.0.0/16",
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True,
            },
        )


class TestSubnetArchitecture:
    """Tests for 3-tier subnet architecture."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for subnet testing."""
        stack = NetworkStack(
            cdk_app,
            "SubnetTestStack",
            env_config=dev_config,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_public_subnets_created(self, template: Template) -> None:
        """Verify public subnets are created with correct configuration."""
        # Public subnets should have MapPublicIpOnLaunch set
        template.has_resource_properties(
            "AWS::EC2::Subnet",
            {
                "MapPublicIpOnLaunch": True,
                "Tags": Match.array_with(
                    [Match.object_like({"Key": "aws-cdk:subnet-type", "Value": "Public"})]
                ),
            },
        )

    def test_private_subnets_created(self, template: Template) -> None:
        """Verify private subnets are created."""
        template.has_resource_properties(
            "AWS::EC2::Subnet",
            {
                "MapPublicIpOnLaunch": False,
                "Tags": Match.array_with(
                    [Match.object_like({"Key": "aws-cdk:subnet-type", "Value": "Private"})]
                ),
            },
        )

    def test_isolated_subnets_created(self, template: Template) -> None:
        """Verify isolated (private-data) subnets are created."""
        template.has_resource_properties(
            "AWS::EC2::Subnet",
            {
                "MapPublicIpOnLaunch": False,
                "Tags": Match.array_with(
                    [Match.object_like({"Key": "aws-cdk:subnet-type", "Value": "Isolated"})]
                ),
            },
        )


class TestNatGatewayConfiguration:
    """Tests for NAT Gateway configuration."""

    def test_dev_single_nat(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify dev environment uses single NAT Gateway for cost savings."""
        stack = NetworkStack(
            cdk_app,
            "DevNatStack",
            env_config=dev_config,
            env=cdk_env,
        )
        template = Template.from_stack(stack)

        # Dev should have 1 NAT Gateway
        template.resource_count_is("AWS::EC2::NatGateway", 1)

    def test_staging_multi_nat(
        self,
        cdk_app: cdk.App,
        staging_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
    ) -> None:
        """Verify staging environment uses multiple NAT Gateways for HA."""
        stack = NetworkStack(
            cdk_app,
            "StagingNatStack",
            env_config=staging_config,
            env=cdk_env,
        )
        template = Template.from_stack(stack)

        # Staging should have 2 NAT Gateways
        template.resource_count_is("AWS::EC2::NatGateway", 2)

    def test_prod_multi_nat(
        self, cdk_app: cdk.App, prod_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify production environment uses multiple NAT Gateways."""
        stack = NetworkStack(
            cdk_app,
            "ProdNatStack",
            env_config=prod_config,
            env=cdk_env,
        )
        template = Template.from_stack(stack)

        # Prod should have 2 NAT Gateways
        template.resource_count_is("AWS::EC2::NatGateway", 2)


class TestVpcEndpoints:
    """Tests for VPC Endpoints."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for VPC endpoint testing."""
        stack = NetworkStack(
            cdk_app,
            "EndpointTestStack",
            env_config=dev_config,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_s3_gateway_endpoint(self, template: Template) -> None:
        """Verify S3 Gateway endpoint is created."""
        template.has_resource_properties(
            "AWS::EC2::VPCEndpoint",
            {
                "VpcEndpointType": "Gateway",
            },
        )

    def test_ecr_interface_endpoints(self, template: Template) -> None:
        """Verify ECR interface endpoints are created."""
        # ECR API endpoint
        template.has_resource_properties(
            "AWS::EC2::VPCEndpoint",
            {
                "VpcEndpointType": "Interface",
                "PrivateDnsEnabled": True,
            },
        )


class TestVpcFlowLogs:
    """Tests for VPC Flow Logs."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for flow log testing."""
        stack = NetworkStack(
            cdk_app,
            "FlowLogTestStack",
            env_config=dev_config,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_flow_logs_enabled(self, template: Template) -> None:
        """Verify VPC Flow Logs are enabled."""
        template.has_resource_properties(
            "AWS::EC2::FlowLog",
            {
                "ResourceType": "VPC",
                "TrafficType": "ALL",
            },
        )


class TestNetworkStackOutputs:
    """Tests for Network Stack outputs."""

    @pytest.fixture
    def network_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> NetworkStack:
        """Create Network Stack for output testing."""
        return NetworkStack(
            cdk_app,
            "OutputTestStack",
            env_config=dev_config,
            env=cdk_env,
        )

    def test_vpc_exported(self, network_stack: NetworkStack) -> None:
        """Verify VPC is accessible from the stack."""
        assert network_stack.vpc is not None

    def test_public_subnets_accessible(self, network_stack: NetworkStack) -> None:
        """Verify public subnets are accessible."""
        assert network_stack.public_subnets is not None

    def test_private_app_subnets_accessible(self, network_stack: NetworkStack) -> None:
        """Verify private app subnets are accessible."""
        assert network_stack.private_app_subnets is not None

    def test_private_data_subnets_accessible(self, network_stack: NetworkStack) -> None:
        """Verify private data subnets are accessible."""
        assert network_stack.private_data_subnets is not None
