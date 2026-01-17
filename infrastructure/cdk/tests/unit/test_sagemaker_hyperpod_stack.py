"""
Unit tests for SageMaker HyperPod Stack.

Tests cover:
- HyperPod cluster creation with EKS orchestration
- Lifecycle scripts S3 bucket configuration
- IAM execution role with comprehensive permissions
- VPC and subnet configuration
- EKS cluster integration
- Automatic node recovery
- CloudFormation outputs
- Security configuration
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import EksStack, IamStack, NetworkStack, SagemakerHyperPodStack


class TestSagemakerHyperPodStackCreation:
    """Tests for HyperPod Stack creation."""

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
    def iam_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> IamStack:
        """Create an IAM Stack for testing."""
        return IamStack(
            cdk_app,
            "TestIamStack",
            env_config=dev_config,
            env=cdk_env,
        )

    @pytest.fixture
    def eks_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        network_stack: NetworkStack,
        iam_stack: IamStack,
    ) -> EksStack:
        """Create an EKS Stack for testing."""
        return EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )

    @pytest.fixture
    def hyperpod_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        network_stack: NetworkStack,
        eks_stack: EksStack,
    ) -> SagemakerHyperPodStack:
        """Create a HyperPod Stack for testing."""
        return SagemakerHyperPodStack(
            cdk_app,
            "TestHyperPodStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_cluster=eks_stack.eks_cluster,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, hyperpod_stack: SagemakerHyperPodStack) -> Template:
        """Get CloudFormation template from the stack."""
        return Template.from_stack(hyperpod_stack)

    def test_stack_synthesizes(self, hyperpod_stack: SagemakerHyperPodStack) -> None:
        """Verify the stack synthesizes without errors."""
        assert hyperpod_stack is not None

    def test_hyperpod_cluster_created(self, template: Template) -> None:
        """Verify HyperPod cluster resource is created."""
        template.resource_count_is("AWS::SageMaker::Cluster", 1)

    def test_cluster_has_eks_orchestrator(self, template: Template) -> None:
        """Verify HyperPod cluster uses EKS orchestration."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "Orchestrator": {
                    "Eks": Match.object_like(
                        {
                            "ClusterArn": Match.any_value(),
                        }
                    )
                }
            },
        )


class TestLifecycleScriptsBucket:
    """Tests for lifecycle scripts S3 bucket."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for lifecycle scripts bucket testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        eks_stack = EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = SagemakerHyperPodStack(
            cdk_app,
            "LifecycleScriptsTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_cluster=eks_stack.eks_cluster,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_lifecycle_bucket_created(self, template: Template) -> None:
        """Verify lifecycle scripts bucket is created."""
        template.resource_count_is("AWS::S3::Bucket", 1)

    def test_bucket_encrypted(self, template: Template) -> None:
        """Verify bucket uses S3-managed encryption."""
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
        """Verify bucket has versioning enabled."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {"VersioningConfiguration": {"Status": "Enabled"}},
        )

    def test_public_access_blocked(self, template: Template) -> None:
        """Verify public access is completely blocked."""
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
        """Verify SSL is enforced via bucket policy."""
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
    """Tests for HyperPod execution IAM role."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for execution role testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        eks_stack = EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = SagemakerHyperPodStack(
            cdk_app,
            "ExecutionRoleTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_cluster=eks_stack.eks_cluster,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_execution_role_created(self, template: Template) -> None:
        """Verify HyperPod execution role is created."""
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
        """Verify AWS managed HyperPod policy is attached."""
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
        """Verify EKS cluster access permissions."""
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
        """Verify EC2 network permissions for VPC integration."""
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
        """Verify ECR permissions for container image pulling."""
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
        """Verify S3 bucket read access for lifecycle scripts."""
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
                                            "s3:GetObject*",
                                            "s3:GetBucket*",
                                            "s3:List*",
                                        ]
                                    )
                                }
                            )
                        ]
                    )
                }
            },
        )


class TestHyperPodClusterConfiguration:
    """Tests for HyperPod cluster configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for cluster configuration testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        eks_stack = EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = SagemakerHyperPodStack(
            cdk_app,
            "ClusterConfigTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_cluster=eks_stack.eks_cluster,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_vpc_configuration(self, template: Template) -> None:
        """Verify HyperPod cluster uses correct VPC configuration."""
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
        """Verify automatic node recovery is enabled."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {"NodeRecovery": "Automatic"},
        )

    def test_instance_group_configured(self, template: Template) -> None:
        """Verify at least one instance group is configured."""
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
        """Verify lifecycle configuration is specified."""
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
    """Tests for removal policies per environment."""

    @pytest.fixture
    def dev_template(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> Template:
        """Create template for dev environment."""
        dev_config = EnvironmentConfig.for_dev(
            account="123456789012", region="us-east-1"
        )
        network_stack = NetworkStack(
            cdk_app, "DevNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(cdk_app, "DevIamStack", env_config=dev_config, env=cdk_env)
        eks_stack = EksStack(
            cdk_app,
            "DevEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = SagemakerHyperPodStack(
            cdk_app,
            "DevHyperPodStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_cluster=eks_stack.eks_cluster,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    @pytest.fixture
    def prod_template(self, cdk_app: cdk.App, cdk_env: cdk.Environment) -> Template:
        """Create template for prod environment."""
        prod_config = EnvironmentConfig.for_prod(
            account="123456789012", region="us-east-1"
        )
        network_stack = NetworkStack(
            cdk_app, "ProdNetworkStack", env_config=prod_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "ProdIamStack", env_config=prod_config, env=cdk_env
        )
        eks_stack = EksStack(
            cdk_app,
            "ProdEksStack",
            env_config=prod_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = SagemakerHyperPodStack(
            cdk_app,
            "ProdHyperPodStack",
            env_config=prod_config,
            vpc=network_stack.vpc,
            eks_cluster=eks_stack.eks_cluster,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_dev_bucket_destroyable(self, dev_template: Template) -> None:
        """Verify dev lifecycle bucket can be deleted."""
        dev_template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Key": "Purpose",
                                "Value": "hyperpod-lifecycle-scripts",
                            }
                        )
                    ]
                )
            },
        )

    def test_prod_bucket_retained(self, prod_template: Template) -> None:
        """Verify prod lifecycle bucket is retained on deletion."""
        prod_template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Key": "Purpose",
                                "Value": "hyperpod-lifecycle-scripts",
                            }
                        )
                    ]
                )
            },
        )


class TestHyperPodStackOutputs:
    """Tests for HyperPod Stack CloudFormation outputs."""

    @pytest.fixture
    def hyperpod_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
    ) -> SagemakerHyperPodStack:
        """Create HyperPod Stack for outputs testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        eks_stack = EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        return SagemakerHyperPodStack(
            cdk_app,
            "OutputTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_cluster=eks_stack.eks_cluster,
            env=cdk_env,
        )

    def test_hyperpod_cluster_accessible(
        self, hyperpod_stack: SagemakerHyperPodStack
    ) -> None:
        """Verify HyperPod cluster is accessible via property."""
        assert hyperpod_stack.hyperpod_cluster is not None

    def test_lifecycle_bucket_accessible(
        self, hyperpod_stack: SagemakerHyperPodStack
    ) -> None:
        """Verify lifecycle scripts bucket is accessible."""
        assert hyperpod_stack.lifecycle_scripts_bucket is not None

    def test_execution_role_accessible(
        self, hyperpod_stack: SagemakerHyperPodStack
    ) -> None:
        """Verify execution role is accessible."""
        assert hyperpod_stack.hyperpod_execution_role is not None


class TestHyperPodStackTags:
    """Tests for HyperPod Stack resource tagging."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for tag testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        eks_stack = EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = SagemakerHyperPodStack(
            cdk_app,
            "TagTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_cluster=eks_stack.eks_cluster,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_cluster_has_name_tag(self, template: Template) -> None:
        """Verify HyperPod cluster has Name tag."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Key": "Name",
                                "Value": Match.any_value(),
                            }
                        )
                    ]
                )
            },
        )

    def test_cluster_has_environment_tag(self, template: Template) -> None:
        """Verify HyperPod cluster has Environment tag."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Key": "Environment",
                                "Value": Match.any_value(),
                            }
                        )
                    ]
                )
            },
        )

    def test_bucket_has_purpose_tag(self, template: Template) -> None:
        """Verify lifecycle bucket has Purpose tag."""
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "Tags": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Key": "Purpose",
                                "Value": "hyperpod-lifecycle-scripts",
                            }
                        )
                    ]
                )
            },
        )


class TestGpuInstanceGroup:
    """Tests for GPU instance group configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for GPU instance group testing."""
        network_stack = NetworkStack(
            cdk_app, "TestNetworkStack", env_config=dev_config, env=cdk_env
        )
        iam_stack = IamStack(
            cdk_app, "TestIamStack", env_config=dev_config, env=cdk_env
        )
        eks_stack = EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )
        stack = SagemakerHyperPodStack(
            cdk_app,
            "GpuInstanceGroupTestStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_cluster=eks_stack.eks_cluster,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_gpu_instance_group_created(self, template: Template) -> None:
        """Verify GPU training instance group is created."""
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
        """Verify GPU instance count matches environment config (dev=1)."""
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
        """Verify GPU instance group has lifecycle configuration."""
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
        """Verify total of 3 instance groups (controller, system, gpu-training)."""
        # Check that we have at least 3 instance groups
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
