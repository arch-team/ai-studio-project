"""SageMaker HyperPod Stack — EKS 编排的 HyperPod 集群。

前提: EKS 集群已部署且 HyperPod Helm Chart 依赖已安装。
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from aws_cdk import aws_sagemaker as sagemaker

from config import EnvironmentConfig
from config.constants import (
    INSTANCE_GROUPS,
    MANAGED_POLICIES,
    SAGEMAKER_INSTANCES,
    TAG_KEYS,
    ProjectPaths,
)
from constructs import Construct
from utils.iam_helpers import (
    add_policy_statement,
    add_policy_statements,
    create_tagged_role,
)
from utils.outputs import create_output
from utils.tagging import create_cfn_tags


class SagemakerHyperPodStack(cdk.Stack):
    """SageMaker HyperPod Stack。"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        eks_cluster: eks.ICluster,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._vpc = vpc
        self._eks_cluster = eks_cluster

        self._lifecycle_scripts_bucket = self._create_lifecycle_scripts_bucket()
        self._hyperpod_execution_role = self._create_hyperpod_execution_role()
        self._hyperpod_cluster = self._create_hyperpod_cluster()
        self._create_outputs()

    def _create_lifecycle_scripts_bucket(self) -> s3.Bucket:
        """创建 HyperPod 生命周期脚本 S3 bucket (存储 on_create.sh 等)。"""
        bucket_name = f"sagemaker-{self.env_config.resource_prefix}-lifecycle"

        bucket = s3.Bucket(
            self,
            "LifecycleScriptsBucket",
            bucket_name=bucket_name,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=self.env_config.protection.removal_policy,
            auto_delete_objects=not self.env_config.protection.retain_on_delete,
        )

        cdk.Tags.of(bucket).add(TAG_KEYS.NAME, bucket_name)
        cdk.Tags.of(bucket).add("Purpose", "hyperpod-lifecycle-scripts")

        s3deploy.BucketDeployment(
            self,
            "DeployLifecycleScripts",
            sources=[s3deploy.Source.asset(str(ProjectPaths.LIFECYCLE_SCRIPTS_DIR))],
            destination_bucket=bucket,
            destination_key_prefix="lifecycle-scripts",
        )

        return bucket

    def _create_hyperpod_execution_role(self) -> iam.Role:
        """创建 HyperPod 执行角色 (S3/CloudWatch/EKS API/VPC 访问)。"""
        role = create_tagged_role(
            scope=self,
            construct_id="HyperPodExecutionRole",
            env_config=self.env_config,
            role_name_suffix="hyperpod-execution-role",
            description="Execution role for SageMaker HyperPod cluster instances",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[MANAGED_POLICIES.SAGEMAKER_CLUSTER_INSTANCE],
        )

        self._lifecycle_scripts_bucket.grant_read(role)

        add_policy_statement(
            role,
            sid="EksClusterAccess",
            actions=[
                "eks:DescribeCluster",
                "eks:ListNodegroups",
                "eks:DescribeNodegroup",
            ],
            resources=[self._eks_cluster.cluster_arn],
        )

        # EKS 编排 HyperPod 所需的 EC2 网络权限
        # https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html
        ec2_network_actions = [
            "ec2:AssignPrivateIpAddresses",
            "ec2:AttachNetworkInterface",
            "ec2:CreateNetworkInterface",
            "ec2:CreateNetworkInterfacePermission",
            "ec2:DeleteNetworkInterface",
            "ec2:DeleteNetworkInterfacePermission",
            "ec2:DescribeInstances",
            "ec2:DescribeInstanceTypes",
            "ec2:DescribeNetworkInterfaces",
            "ec2:DescribeTags",
            "ec2:DescribeVpcs",
            "ec2:DescribeDhcpOptions",
            "ec2:DescribeSubnets",
            "ec2:DescribeSecurityGroups",
            "ec2:DetachNetworkInterface",
            "ec2:ModifyNetworkInterfaceAttribute",
            "ec2:UnassignPrivateIpAddresses",
        ]

        add_policy_statements(
            role,
            [
                ("Ec2NetworkAccess", ec2_network_actions, ["*"]),
                (
                    "Ec2CreateTags",
                    ["ec2:CreateTags"],
                    ["arn:aws:ec2:*:*:network-interface/*"],
                ),
                (
                    "EcrAccess",
                    [
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:BatchGetImage",
                        "ecr:GetAuthorizationToken",
                        "ecr:GetDownloadUrlForLayer",
                    ],
                    ["*"],
                ),
                ("EksPodIdentity", ["eks-auth:AssumeRoleForPodIdentity"], ["*"]),
            ],
        )

        return role

    def _create_instance_group(
        self,
        name: str,
        instance_type: str,
        instance_count: int = 1,
    ) -> sagemaker.CfnCluster.ClusterInstanceGroupProperty:
        """创建 HyperPod 实例组配置。"""
        return sagemaker.CfnCluster.ClusterInstanceGroupProperty(
            instance_group_name=name,
            instance_type=instance_type,
            instance_count=instance_count,
            life_cycle_config=sagemaker.CfnCluster.ClusterLifeCycleConfigProperty(
                source_s3_uri=f"s3://{self._lifecycle_scripts_bucket.bucket_name}/lifecycle-scripts",
                on_create="on_create.sh",
            ),
            execution_role=self._hyperpod_execution_role.role_arn,
        )

    def _create_hyperpod_cluster(self) -> sagemaker.CfnCluster:
        """创建 SageMaker HyperPod 集群 (EKS 编排)。"""
        private_subnet_ids = [subnet.subnet_id for subnet in self._vpc.private_subnets]
        security_group_ids = [self._eks_cluster.cluster_security_group_id]

        instance_groups = [
            self._create_instance_group(
                name=INSTANCE_GROUPS.CONTROLLER,
                instance_type=SAGEMAKER_INSTANCES.CONTROLLER,
                instance_count=1,
            ),
            # ml.m5.4xlarge supports ~234 pods (8 ENIs × 30 IPs per ENI)
            self._create_instance_group(
                name=INSTANCE_GROUPS.SYSTEM,
                instance_type=SAGEMAKER_INSTANCES.SYSTEM,
                instance_count=1,
            ),
        ]

        gpu_config = self.env_config.eks.gpu_instance_group
        if gpu_config.enabled:
            instance_groups.append(
                self._create_instance_group(
                    name=INSTANCE_GROUPS.GPU_TRAINING,
                    instance_type=SAGEMAKER_INSTANCES.GPU_G5_2XLARGE,
                    instance_count=gpu_config.instance_count,
                )
            )

        cluster = sagemaker.CfnCluster(
            self,
            "HyperPodCluster",
            cluster_name=f"{self.env_config.resource_prefix}-hyperpod",
            instance_groups=instance_groups,
            vpc_config=sagemaker.CfnCluster.VpcConfigProperty(
                security_group_ids=security_group_ids,
                subnets=private_subnet_ids,
            ),
            orchestrator=sagemaker.CfnCluster.OrchestratorProperty(
                eks=sagemaker.CfnCluster.ClusterOrchestratorEksConfigProperty(
                    cluster_arn=self._eks_cluster.cluster_arn,
                )
            ),
            node_recovery="Automatic",
            # SageMaker=true is required by AmazonSageMakerHyperPodTrainingOperatorAccess policy
            tags=create_cfn_tags(
                self.env_config,
                "hyperpod",
                additional_tags={TAG_KEYS.SAGEMAKER: "true"},
            ),
        )

        cluster.node.add_dependency(self._hyperpod_execution_role)

        return cluster

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出。"""
        create_output(
            self,
            "HyperPodClusterArn",
            self._hyperpod_cluster.attr_cluster_arn,
            "SageMaker HyperPod cluster ARN",
            export_name=f"{self.env_config.resource_prefix}-hyperpod-arn",
        )

        create_output(
            self,
            "LifecycleScriptsBucketName",
            self._lifecycle_scripts_bucket.bucket_name,
            "S3 bucket for HyperPod lifecycle scripts",
            export_name=f"{self.env_config.resource_prefix}-lifecycle-bucket",
        )

        create_output(
            self,
            "HyperPodExecutionRoleArn",
            self._hyperpod_execution_role.role_arn,
            "HyperPod execution role ARN",
            export_name=f"{self.env_config.resource_prefix}-hyperpod-execution-role-arn",
        )

    @property
    def hyperpod_cluster(self) -> sagemaker.CfnCluster:
        return self._hyperpod_cluster

    @property
    def lifecycle_scripts_bucket(self) -> s3.Bucket:
        return self._lifecycle_scripts_bucket

    @property
    def hyperpod_execution_role(self) -> iam.Role:
        return self._hyperpod_execution_role
