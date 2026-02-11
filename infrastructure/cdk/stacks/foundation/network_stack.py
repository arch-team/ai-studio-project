"""Network Stack — 3 层子网隔离 VPC。

Public (NAT/ALB) / PrivateApp (EKS) / PrivateData (FSx/Aurora)。
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2

from config import DeploymentMode, EnvironmentConfig
from constructs import Construct
from utils.outputs import create_output


class NetworkStack(cdk.Stack):
    """VPC Stack — 3 层子网隔离 + VPC Endpoints。"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config

        self.vpc = self._create_vpc()
        self._vpc_endpoint_sg = self._create_vpc_endpoint_security_group()
        self._create_vpc_endpoints()
        self._create_outputs()

    def _create_vpc(self) -> ec2.Vpc:
        """创建 3 层子网隔离 VPC (按 plan.md 分配子网比例)。"""
        vpc_config = self.env_config.vpc

        max_azs = self._get_azs_for_deployment_mode(vpc_config.deployment_mode)

        subnet_configuration = [
            ec2.SubnetConfiguration(
                name="Public",
                subnet_type=ec2.SubnetType.PUBLIC,
                cidr_mask=20,
            ),
            ec2.SubnetConfiguration(
                name="PrivateApp",
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                cidr_mask=19,
            ),
            ec2.SubnetConfiguration(
                name="PrivateData",
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                cidr_mask=20,
            ),
        ]

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
            restrict_default_security_group=True,
        )

        vpc.add_flow_log(
            "FlowLog",
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        cdk.Tags.of(vpc).add("Name", f"{self.env_config.resource_prefix}-vpc")
        cdk.Tags.of(vpc).add("DeploymentMode", vpc_config.deployment_mode.value)

        self._validate_subnet_capacity(vpc)

        return vpc

    def _get_azs_for_deployment_mode(self, mode: DeploymentMode) -> int:
        """根据部署模式返回 AZ 数量。"""
        az_mapping = {
            DeploymentMode.SINGLE_AZ: 1,
            DeploymentMode.MULTI_AZ: 3,
            DeploymentMode.HYBRID: 3,  # 3 AZs for compute, data layer uses affinity
        }
        return az_mapping.get(mode, 3)

    def _validate_subnet_capacity(self, _vpc: ec2.Vpc) -> None:
        """验证子网容量满足节点扩展需求 (≥1000 节点)。

        /19 子网: 8,192 IPs x 3 AZs / 20 IPs per node ≈ 1,228 节点。
        """
        cdk.Annotations.of(self).add_info(
            "VPC Capacity: /19 private app subnets support ~1,200+ nodes "
            "(8,192 IPs × 3 AZs / 20 IPs per node)"
        )

    def _create_vpc_endpoint_security_group(self) -> ec2.SecurityGroup:
        """创建 VPC Endpoint 安全组。

        仅允许 Private/Isolated 子网的 HTTPS (443) 访问 (最小权限)。
        Public 子网通过 NAT Gateway 访问 AWS 服务，无需 VPC Endpoint。
        """
        sg = ec2.SecurityGroup(
            self,
            "VpcEndpointSg",
            vpc=self.vpc,
            security_group_name=f"{self.env_config.resource_prefix}-vpce-sg",
            description="Security group for VPC endpoints",
            allow_all_outbound=False,
        )

        for subnet in self.vpc.private_subnets + self.vpc.isolated_subnets:
            sg.add_ingress_rule(
                peer=ec2.Peer.ipv4(subnet.ipv4_cidr_block),
                connection=ec2.Port.tcp(443),
                description=f"Allow HTTPS from {subnet.node.id}",
            )

        cdk.Tags.of(sg).add("Name", f"{self.env_config.resource_prefix}-vpce-sg")

        return sg

    def _create_vpc_endpoints(self) -> None:
        """创建 VPC Endpoints (Gateway: S3; Interface: ECR/CloudWatch/STS/SageMaker/EFS)。"""
        # S3 Gateway endpoint (免费)
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            ],
        )

        interface_endpoints = [
            ("EcrApi", ec2.InterfaceVpcEndpointAwsService.ECR),
            ("EcrDkr", ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER),
            ("CloudWatchLogs", ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS),
            ("CloudWatchMonitoring", ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH),
            ("Sts", ec2.InterfaceVpcEndpointAwsService.STS),
            ("SageMakerApi", ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_API),
            ("SageMakerRuntime", ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_RUNTIME),
            ("Efs", ec2.InterfaceVpcEndpointAwsService.ELASTIC_FILESYSTEM),
            ("Ssm", ec2.InterfaceVpcEndpointAwsService.SSM),
            ("SsmMessages", ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES),
            ("Ec2Messages", ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES),
        ]

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
        """创建 CloudFormation 输出。"""
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
            export_name=f"{self.env_config.resource_prefix}-vpce-sg-id",
        )

    @property
    def public_subnets(self) -> ec2.SubnetSelection:
        return ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)

    @property
    def private_app_subnets(self) -> ec2.SubnetSelection:
        return ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)

    @property
    def private_data_subnets(self) -> ec2.SubnetSelection:
        return ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)

    @property
    def vpc_endpoint_sg(self) -> ec2.SecurityGroup:
        return self._vpc_endpoint_sg
