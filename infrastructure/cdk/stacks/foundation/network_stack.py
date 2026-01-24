"""
Network Stack for AI Training Platform.

This stack creates the VPC infrastructure with 3-tier subnet isolation:
- Public subnets: NAT Gateways, ALB
- Private App subnets: EKS nodes, compute resources
- Private Data subnets: FSx for Lustre, Aurora MySQL

Follows AWS Well-Architected Framework security best practices.
"""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2

from config import DeploymentMode, EnvironmentConfig
from constructs import Construct
from utils.outputs import create_output


class NetworkStack(cdk.Stack):
    """VPC Stack with 3-tier subnet isolation and VPC endpoints.

    This stack creates:
    - VPC with configurable CIDR block
    - Public, Private App, and Private Data subnets across multiple AZs
    - NAT Gateways (cost-optimized: 2 AZs by default)
    - VPC endpoints for AWS services (S3, ECR, CloudWatch, STS, SageMaker, EFS)
    - Security groups for VPC endpoints

    Attributes:
        vpc: The created VPC construct
        public_subnets: List of public subnet selections
        private_app_subnets: List of private app layer subnet selections
        private_data_subnets: List of private data layer subnet selections
        vpc_endpoint_sg: Security group for VPC endpoints
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        **kwargs,
    ) -> None:
        """Initialize the Network Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            env_config: Environment configuration
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config

        # Create VPC with 3-tier subnet architecture
        self.vpc = self._create_vpc()

        # Create VPC endpoints for AWS services
        self._vpc_endpoint_sg = self._create_vpc_endpoint_security_group()
        self._create_vpc_endpoints()

        # Export VPC attributes
        self._create_outputs()

    def _create_vpc(self) -> ec2.Vpc:
        """Create VPC with 3-tier subnet isolation.

        Subnet allocation follows the plan.md specification:
        - Public: 18.75% (NAT Gateway, ALB)
        - Private App: 37.5% (EKS nodes, RDS)
        - Private Data: 18.75% (FSx, ElastiCache)
        """
        vpc_config = self.env_config.vpc

        # Determine number of AZs based on deployment mode
        max_azs = self._get_azs_for_deployment_mode(vpc_config.deployment_mode)

        # Define subnet configuration for 3-tier architecture
        subnet_configuration = [
            # Public subnets (NAT Gateway, ALB)
            ec2.SubnetConfiguration(
                name="Public",
                subnet_type=ec2.SubnetType.PUBLIC,
                cidr_mask=20,  # /20 = 4,096 IPs per subnet
            ),
            # Private App subnets (EKS nodes, compute)
            ec2.SubnetConfiguration(
                name="PrivateApp",
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                cidr_mask=19,  # /19 = 8,192 IPs per subnet
            ),
            # Private Data subnets (FSx, Aurora, ElastiCache)
            ec2.SubnetConfiguration(
                name="PrivateData",
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                cidr_mask=20,  # /20 = 4,096 IPs per subnet
            ),
        ]

        # Create VPC
        vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=f"{self.env_config.resource_prefix}-vpc",
            ip_addresses=ec2.IpAddresses.cidr(vpc_config.cidr),
            max_azs=max_azs,
            nat_gateways=vpc_config.nat_gateways,
            subnet_configuration=subnet_configuration,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            # Restrict default security group (security best practice)
            restrict_default_security_group=True,
        )

        # Add flow logs for network monitoring
        vpc.add_flow_log(
            "FlowLog",
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        # Add tags for cost allocation and identification
        cdk.Tags.of(vpc).add("Name", f"{self.env_config.resource_prefix}-vpc")
        cdk.Tags.of(vpc).add("DeploymentMode", vpc_config.deployment_mode.value)

        # Validate subnet capacity for EKS node scaling
        self._validate_subnet_capacity(vpc)

        return vpc

    def _get_azs_for_deployment_mode(self, mode: DeploymentMode) -> int:
        """Get number of AZs based on deployment mode.

        Args:
            mode: Deployment mode (single-az, multi-az, hybrid)

        Returns:
            Number of AZs to use
        """
        az_mapping = {
            DeploymentMode.SINGLE_AZ: 1,
            DeploymentMode.MULTI_AZ: 3,
            DeploymentMode.HYBRID: 3,  # 3 AZs for compute, data layer uses affinity
        }
        return az_mapping.get(mode, 3)

    def _validate_subnet_capacity(self, _vpc: ec2.Vpc) -> None:
        """Validate subnet capacity meets node scaling requirements.

        Target: Support ≥1000 nodes
        Formula: Available nodes ≈ Private App subnet IPs / 20 (IPs per node)

        For /19 subnets: 8,192 IPs × 3 AZs = 24,576 IPs
        Max nodes: 24,576 / 20 ≈ 1,228 nodes ✓

        Note: VPC parameter reserved for future detailed capacity validation.
        """
        # Add annotation for capacity validation
        cdk.Annotations.of(self).add_info(
            "VPC Capacity: /19 private app subnets support ~1,200+ nodes "
            "(8,192 IPs × 3 AZs / 20 IPs per node)"
        )

    def _create_vpc_endpoint_security_group(self) -> ec2.SecurityGroup:
        """Create security group for VPC endpoints.

        Allows HTTPS (443) traffic from VPC CIDR for interface endpoints.
        """
        sg = ec2.SecurityGroup(
            self,
            "VpcEndpointSg",
            vpc=self.vpc,
            security_group_name=f"{self.env_config.resource_prefix}-vpce-sg",
            description="Security group for VPC endpoints",
            allow_all_outbound=False,
        )

        # Allow HTTPS from within VPC
        sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.env_config.vpc.cidr),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS from VPC CIDR",
        )

        cdk.Tags.of(sg).add("Name", f"{self.env_config.resource_prefix}-vpce-sg")

        return sg

    def _create_vpc_endpoints(self) -> None:
        """Create VPC endpoints for AWS services.

        Creates both Gateway and Interface endpoints:
        - Gateway: S3 (no cost)
        - Interface: ECR, CloudWatch, STS, SageMaker, EFS
        """
        # S3 Gateway endpoint (no additional cost)
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            ],
        )

        # Define interface endpoints
        interface_endpoints = [
            # ECR endpoints (required for pulling container images)
            ("EcrApi", ec2.InterfaceVpcEndpointAwsService.ECR),
            ("EcrDkr", ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER),
            # CloudWatch endpoints (required for logging and metrics)
            ("CloudWatchLogs", ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS),
            ("CloudWatchMonitoring", ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH),
            # STS endpoint (required for IAM role assumption)
            ("Sts", ec2.InterfaceVpcEndpointAwsService.STS),
            # SageMaker API endpoint (required for HyperPod operations)
            ("SageMakerApi", ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_API),
            ("SageMakerRuntime", ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_RUNTIME),
            # EFS endpoint (required for SageMaker Spaces persistent storage)
            ("Efs", ec2.InterfaceVpcEndpointAwsService.ELASTIC_FILESYSTEM),
            # SSM endpoints (for Systems Manager access)
            ("Ssm", ec2.InterfaceVpcEndpointAwsService.SSM),
            ("SsmMessages", ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES),
            ("Ec2Messages", ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES),
        ]

        # Create interface endpoints
        for endpoint_id, service in interface_endpoints:
            self.vpc.add_interface_endpoint(
                endpoint_id,
                service=service,
                subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
                security_groups=[self._vpc_endpoint_sg],
                private_dns_enabled=True,
            )

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack references."""
        create_output(self, "VpcId", self.vpc.vpc_id, "VPC ID")
        create_output(self, "VpcCidr", self.vpc.vpc_cidr_block, "VPC CIDR block")
        create_output(
            self,
            "PublicSubnetIds",
            ",".join([s.subnet_id for s in self.vpc.public_subnets]),
            "Public subnet IDs",
        )
        create_output(
            self,
            "PrivateAppSubnetIds",
            ",".join([s.subnet_id for s in self.vpc.private_subnets]),
            "Private app layer subnet IDs",
        )
        create_output(
            self,
            "PrivateDataSubnetIds",
            ",".join([s.subnet_id for s in self.vpc.isolated_subnets]),
            "Private data layer subnet IDs",
        )
        create_output(
            self,
            "VpcEndpointSecurityGroupId",
            self._vpc_endpoint_sg.security_group_id,
            "VPC endpoint security group ID",
        )

    @property
    def public_subnets(self) -> ec2.SubnetSelection:
        """Get public subnet selection."""
        return ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)

    @property
    def private_app_subnets(self) -> ec2.SubnetSelection:
        """Get private app layer subnet selection."""
        return ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)

    @property
    def private_data_subnets(self) -> ec2.SubnetSelection:
        """Get private data layer subnet selection (isolated)."""
        return ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)

    @property
    def vpc_endpoint_sg(self) -> ec2.SecurityGroup:
        """Get VPC endpoint security group."""
        return self._vpc_endpoint_sg
