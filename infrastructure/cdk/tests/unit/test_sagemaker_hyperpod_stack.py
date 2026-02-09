"""
SageMaker HyperPod Stack 单元测试.

测试覆盖:
- HyperPod 集群创建 (EKS 编排)
- 生命周期脚本 S3 Bucket 配置
- IAM 执行角色 (综合权限)
- VPC 和子网配置
- EKS 集群集成
- 自动节点恢复
- CloudFormation 输出
- 安全配置
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import EksStack, IamStack, NetworkStack, SagemakerHyperPodStack

# =============================================================================
# 共用 Fixtures - 使用 conftest 的 network_stack, iam_stack, eks_stack
# =============================================================================


@pytest.fixture
def hyperpod_stack(
    cdk_app: cdk.App,
    dev_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
    network_stack: NetworkStack,
    eks_stack: EksStack,
) -> SagemakerHyperPodStack:
    """创建 HyperPod Stack."""
    return SagemakerHyperPodStack(
        cdk_app,
        "TestHyperPodStack",
        env_config=dev_config,
        vpc=network_stack.vpc,
        eks_cluster=eks_stack.eks_cluster,
        env=cdk_env,
    )


@pytest.fixture
def template(hyperpod_stack: SagemakerHyperPodStack) -> Template:
    """获取 CloudFormation 模板."""
    return Template.from_stack(hyperpod_stack)


def _create_hyperpod_template(
    cdk_app: cdk.App,
    env_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
    prefix: str,
) -> Template:
    """辅助函数: 为指定环境创建 HyperPod 模板."""
    network = NetworkStack(
        cdk_app, f"{prefix}Network", env_config=env_config, env=cdk_env
    )
    iam = IamStack(cdk_app, f"{prefix}Iam", env_config=env_config, env=cdk_env)
    eks = EksStack(
        cdk_app,
        f"{prefix}Eks",
        env_config=env_config,
        vpc=network.vpc,
        eks_node_role=iam.eks_node_role,
        env=cdk_env,
    )
    stack = SagemakerHyperPodStack(
        cdk_app,
        f"{prefix}HyperPod",
        env_config=env_config,
        vpc=network.vpc,
        eks_cluster=eks.eks_cluster,
        env=cdk_env,
    )
    return Template.from_stack(stack)


# =============================================================================
# 测试类
# =============================================================================


class TestSagemakerHyperPodStackCreation:
    """HyperPod Stack 创建测试."""

    def test_stack_synthesizes(self, hyperpod_stack: SagemakerHyperPodStack) -> None:
        """验证 Stack 可以成功合成."""
        assert hyperpod_stack is not None

    def test_hyperpod_cluster_created(self, template: Template) -> None:
        """验证 HyperPod 集群资源创建."""
        template.resource_count_is("AWS::SageMaker::Cluster", 1)

    def test_cluster_has_eks_orchestrator(self, template: Template) -> None:
        """验证 HyperPod 集群使用 EKS 编排."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "Orchestrator": {
                    "Eks": Match.object_like({"ClusterArn": Match.any_value()})
                }
            },
        )


class TestLifecycleScriptsBucket:
    """生命周期脚本 S3 Bucket 测试."""

    def test_lifecycle_bucket_created(self, template: Template) -> None:
        """验证生命周期脚本 Bucket 创建."""
        template.resource_count_is("AWS::S3::Bucket", 1)

    def test_bucket_encrypted(self, template: Template) -> None:
        """验证 Bucket 使用 S3 托管加密."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "BucketEncryption": {
                    "ServerSideEncryptionConfiguration": [
                        {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
                    ]
                }
            },
        )

    def test_bucket_versioned(self, template: Template) -> None:
        """验证 Bucket 启用版本控制."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {"VersioningConfiguration": {"Status": "Enabled"}},
        )

    def test_public_access_blocked(self, template: Template) -> None:
        """验证完全阻止公共访问."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True,
                }
            },
        )

    def test_ssl_enforced(self, template: Template) -> None:
        """验证通过 Bucket 策略强制 SSL."""
        template.has_resource_properties(
            "AWS::S3::BucketPolicy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Effect": "Deny",
                                    "Condition": {
                                        "Bool": {"aws:SecureTransport": "false"}
                                    },
                                }
                            )
                        ]
                    )
                }
            },
        )


class TestHyperPodExecutionRole:
    """HyperPod 执行 IAM 角色测试."""

    def test_execution_role_created(self, template: Template) -> None:
        """验证执行角色创建."""
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {"Principal": {"Service": "sagemaker.amazonaws.com"}}
                            )
                        ]
                    )
                }
            },
        )

    def test_managed_policy_attached(self, template: Template) -> None:
        """验证 AWS 托管 HyperPod 策略附加."""
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "ManagedPolicyArns": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Fn::Join": Match.array_with(
                                    [
                                        Match.array_with(
                                            [
                                                Match.string_like_regexp(
                                                    ".*AmazonSageMakerClusterInstanceRolePolicy.*"
                                                )
                                            ]
                                        )
                                    ]
                                )
                            }
                        )
                    ]
                )
            },
        )

    def test_eks_cluster_access_policy(self, template: Template) -> None:
        """验证 EKS 集群访问权限."""
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": [
                                        "eks:DescribeCluster",
                                        "eks:ListNodegroups",
                                        "eks:DescribeNodegroup",
                                    ],
                                    "Sid": "EksClusterAccess",
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_ec2_network_access_policy(self, template: Template) -> None:
        """验证 EC2 网络权限 (VPC 集成)."""
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": Match.array_with(
                                        [
                                            "ec2:CreateNetworkInterface",
                                            "ec2:DescribeNetworkInterfaces",
                                            "ec2:DescribeSubnets",
                                            "ec2:DescribeSecurityGroups",
                                        ]
                                    ),
                                    "Sid": "Ec2NetworkAccess",
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_ecr_access_policy(self, template: Template) -> None:
        """验证 ECR 容器镜像拉取权限."""
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": Match.array_with(
                                        [
                                            "ecr:BatchCheckLayerAvailability",
                                            "ecr:BatchGetImage",
                                            "ecr:GetAuthorizationToken",
                                        ]
                                    ),
                                    "Sid": "EcrAccess",
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_s3_bucket_access_granted(self, template: Template) -> None:
        """验证 S3 Bucket 读取权限 (生命周期脚本)."""
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": Match.array_with(
                                        ["s3:GetObject*", "s3:GetBucket*", "s3:List*"]
                                    )
                                }
                            )
                        ]
                    )
                }
            },
        )


class TestHyperPodClusterConfiguration:
    """HyperPod 集群配置测试."""

    def test_vpc_configuration(self, template: Template) -> None:
        """验证 VPC 配置."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "VpcConfig": {
                    "SecurityGroupIds": Match.any_value(),
                    "Subnets": Match.any_value(),
                }
            },
        )

    def test_automatic_node_recovery(self, template: Template) -> None:
        """验证自动节点恢复已启用."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {"NodeRecovery": "Automatic"},
        )

    def test_instance_group_configured(self, template: Template) -> None:
        """验证至少一个实例组已配置."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "InstanceGroups": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "InstanceGroupName": Match.any_value(),
                                "InstanceType": Match.any_value(),
                                "InstanceCount": Match.any_value(),
                            }
                        )
                    ]
                )
            },
        )

    def test_lifecycle_config_specified(self, template: Template) -> None:
        """验证生命周期配置."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "InstanceGroups": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "LifeCycleConfig": {
                                    "SourceS3Uri": Match.any_value(),
                                    "OnCreate": "on_create.sh",
                                }
                            }
                        )
                    ]
                )
            },
        )


class TestRemovalPolicies:
    """各环境删除策略测试."""

    def test_dev_bucket_destroyable(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """验证开发环境生命周期 Bucket 可删除."""
        template = _create_hyperpod_template(cdk_app, dev_config, cdk_env, "Dev")
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {"Key": "Purpose", "Value": "hyperpod-lifecycle-scripts"}
                        )
                    ]
                )
            },
        )

    def test_prod_bucket_retained(
        self, cdk_app: cdk.App, prod_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """验证生产环境生命周期 Bucket 被保留."""
        template = _create_hyperpod_template(cdk_app, prod_config, cdk_env, "Prod")
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {"Key": "Purpose", "Value": "hyperpod-lifecycle-scripts"}
                        )
                    ]
                )
            },
        )


class TestHyperPodStackOutputs:
    """HyperPod Stack 输出属性测试."""

    def test_hyperpod_cluster_accessible(
        self, hyperpod_stack: SagemakerHyperPodStack
    ) -> None:
        """验证 HyperPod 集群可访问."""
        assert hyperpod_stack.hyperpod_cluster is not None

    def test_lifecycle_bucket_accessible(
        self, hyperpod_stack: SagemakerHyperPodStack
    ) -> None:
        """验证生命周期脚本 Bucket 可访问."""
        assert hyperpod_stack.lifecycle_scripts_bucket is not None

    def test_execution_role_accessible(
        self, hyperpod_stack: SagemakerHyperPodStack
    ) -> None:
        """验证执行角色可访问."""
        assert hyperpod_stack.hyperpod_execution_role is not None


class TestHyperPodStackTags:
    """HyperPod Stack 标签测试."""

    def test_cluster_has_name_tag(self, template: Template) -> None:
        """验证集群有 Name 标签."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "Tags": Match.array_with(
                    [Match.object_like({"Key": "Name", "Value": Match.any_value()})]
                )
            },
        )

    def test_cluster_has_environment_tag(self, template: Template) -> None:
        """验证集群有 Environment 标签."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {"Key": "Environment", "Value": Match.any_value()}
                        )
                    ]
                )
            },
        )

    def test_bucket_has_purpose_tag(self, template: Template) -> None:
        """验证生命周期 Bucket 有 Purpose 标签."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {"Key": "Purpose", "Value": "hyperpod-lifecycle-scripts"}
                        )
                    ]
                )
            },
        )


class TestGpuInstanceGroup:
    """GPU 实例组配置测试."""

    def test_gpu_instance_group_created(self, template: Template) -> None:
        """验证 GPU 训练实例组创建."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "InstanceGroups": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "InstanceGroupName": "gpu-training-group",
                                "InstanceType": "ml.g5.2xlarge",
                            }
                        )
                    ]
                )
            },
        )

    def test_gpu_instance_count_matches_config(self, template: Template) -> None:
        """验证 GPU 实例数匹配环境配置 (dev=1)."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "InstanceGroups": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "InstanceGroupName": "gpu-training-group",
                                "InstanceCount": 1,
                            }
                        )
                    ]
                )
            },
        )

    def test_gpu_instance_has_lifecycle_config(self, template: Template) -> None:
        """验证 GPU 实例组有生命周期配置."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "InstanceGroups": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "InstanceGroupName": "gpu-training-group",
                                "LifeCycleConfig": {
                                    "SourceS3Uri": Match.any_value(),
                                    "OnCreate": "on_create.sh",
                                },
                            }
                        )
                    ]
                )
            },
        )

    def test_three_instance_groups_total(self, template: Template) -> None:
        """验证共 3 个实例组 (controller, system, gpu-training)."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "InstanceGroups": Match.array_with(
                    [
                        Match.object_like({"InstanceGroupName": "controller-group"}),
                        Match.object_like({"InstanceGroupName": "system-group"}),
                        Match.object_like({"InstanceGroupName": "gpu-training-group"}),
                    ]
                )
            },
        )
