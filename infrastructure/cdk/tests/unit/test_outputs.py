"""
to_kebab_case 函数单元测试.

测试覆盖:
- 标准 PascalCase/camelCase 转换
- 缩写词处理 (全大写: EKS, ARN, VPC; 混合大小写: GiB, MBps)
- 边界场景 (纯大写、纯小写、数字混合)
- 所有现有 Stack output_id 的转换结果回归保护
"""

import pytest

from utils.outputs import to_kebab_case


class TestToKebabCaseBasic:
    """基础 PascalCase/camelCase 转换测试."""

    def test_simple_pascal_case(self) -> None:
        """PascalCase 转换."""
        assert to_kebab_case("ClusterEndpoint") == "cluster-endpoint"

    def test_camel_case(self) -> None:
        """camelCase 转换."""
        assert to_kebab_case("vpcId") == "vpc-id"

    def test_single_word(self) -> None:
        """单个单词转换."""
        assert to_kebab_case("Cluster") == "cluster"

    def test_already_lowercase(self) -> None:
        """纯小写输入."""
        assert to_kebab_case("cluster") == "cluster"

    def test_multi_word_pascal(self) -> None:
        """多词 PascalCase."""
        assert (
            to_kebab_case("VpcEndpointSecurityGroupId")
            == "vpc-endpoint-security-group-id"
        )


class TestToKebabCaseAllUpperAbbreviations:
    """全大写缩写词测试 (EKS, ARN, VPC 等)."""

    def test_eks_prefix(self) -> None:
        """EKS 前缀缩写."""
        assert to_kebab_case("EKSClusterARN") == "eks-cluster-arn"

    def test_trailing_arn(self) -> None:
        """尾部 ARN 缩写."""
        assert to_kebab_case("EksClusterArn") == "eks-cluster-arn"

    def test_vpc_prefix(self) -> None:
        """VPC 前缀."""
        assert to_kebab_case("VpcId") == "vpc-id"

    def test_alb_prefix(self) -> None:
        """ALB 前缀."""
        assert to_kebab_case("AlbDnsName") == "alb-dns-name"

    def test_oidc_embedded(self) -> None:
        """嵌入式 OIDC 缩写."""
        assert to_kebab_case("EksOidcProviderArn") == "eks-oidc-provider-arn"

    def test_all_uppercase(self) -> None:
        """纯大写输入."""
        assert to_kebab_case("ARN") == "arn"

    def test_all_uppercase_multi(self) -> None:
        """纯大写多字母."""
        assert to_kebab_case("VPCARN") == "vpcarn"


class TestToKebabCaseMixedAbbreviations:
    """混合大小写缩写词测试 (GiB, MBps 等) - 核心修复场景."""

    def test_gib_suffix(self) -> None:
        """GiB 后缀正确处理."""
        assert to_kebab_case("StorageCapacityGiB") == "storage-capacity-gib"

    def test_mbps_suffix(self) -> None:
        """MBps 后缀正确处理."""
        assert to_kebab_case("TotalThroughputMBps") == "total-throughput-mbps"

    def test_mib_suffix(self) -> None:
        """MiB 后缀正确处理."""
        assert to_kebab_case("MemoryLimitMiB") == "memory-limit-mib"

    def test_tib_suffix(self) -> None:
        """TiB 后缀正确处理."""
        assert to_kebab_case("DiskCapacityTiB") == "disk-capacity-tib"

    def test_gib_in_middle(self) -> None:
        """GiB 在中间位置."""
        assert to_kebab_case("StorageGiBCapacity") == "storage-gib-capacity"


class TestToKebabCaseNumbers:
    """数字混合场景测试."""

    def test_number_suffix(self) -> None:
        """数字后缀."""
        assert to_kebab_case("Ec2InstanceType") == "ec2-instance-type"

    def test_number_in_middle(self) -> None:
        """数字在中间."""
        assert to_kebab_case("S3BucketName") == "s3-bucket-name"


class TestToKebabCaseExistingOutputIds:
    """所有现有 Stack output_id 的回归测试.

    确保修复缩写词处理后，不影响现有的 output_id 转换结果。
    注意: database_stack 和 fsx_stack 使用显式 export_name，
    此处仅验证 to_kebab_case 函数的转换结果一致性。
    """

    # (output_id, 期望的 kebab-case 结果)
    @pytest.mark.parametrize(
        ("output_id", "expected"),
        [
            # NetworkStack
            ("VpcId", "vpc-id"),
            ("VpcCidr", "vpc-cidr"),
            ("PublicSubnetIds", "public-subnet-ids"),
            ("PrivateAppSubnetIds", "private-app-subnet-ids"),
            ("PrivateDataSubnetIds", "private-data-subnet-ids"),
            ("VpcEndpointSecurityGroupId", "vpc-endpoint-security-group-id"),
            # IamStack
            ("EksNodeRoleArn", "eks-node-role-arn"),
            ("EksNodeRoleName", "eks-node-role-name"),
            ("TrainingExecutionRoleArn", "training-execution-role-arn"),
            ("BackendServiceRoleArn", "backend-service-role-arn"),
            # EksStack
            ("EksClusterName", "eks-cluster-name"),
            ("EksClusterArn", "eks-cluster-arn"),
            ("EksClusterEndpoint", "eks-cluster-endpoint"),
            ("EksClusterSecurityGroupId", "eks-cluster-security-group-id"),
            ("EksOidcProviderArn", "eks-oidc-provider-arn"),
            ("CertManagerAddonName", "cert-manager-addon-name"),
            # SagemakerHyperPodStack
            ("HyperPodClusterArn", "hyper-pod-cluster-arn"),
            ("LifecycleScriptsBucketName", "lifecycle-scripts-bucket-name"),
            ("HyperPodExecutionRoleArn", "hyper-pod-execution-role-arn"),
            # HyperPodAddonsStack
            ("TrainingOperatorAddonName", "training-operator-addon-name"),
            ("TaskGovernanceAddonName", "task-governance-addon-name"),
            # ObservabilityStack
            ("AmpWorkspaceArn", "amp-workspace-arn"),
            ("AmpWorkspaceId", "amp-workspace-id"),
            ("AmpRemoteWriteEndpoint", "amp-remote-write-endpoint"),
            ("ObservabilityAddonName", "observability-addon-name"),
            # ApplicationStack
            ("BackendRepositoryUri", "backend-repository-uri"),
            ("BackendRepositoryArn", "backend-repository-arn"),
            # AlbStack
            ("AlbDnsName", "alb-dns-name"),
            ("AlbArn", "alb-arn"),
            ("HttpsListenerArn", "https-listener-arn"),
            ("HttpListenerArn", "http-listener-arn"),
            ("BackendTargetGroupArn", "backend-target-group-arn"),
            ("FrontendTargetGroupArn", "frontend-target-group-arn"),
            ("SecurityGroupId", "security-group-id"),
            # StorageStack (动态生成的 output_id)
            ("DatasetsBucketName", "datasets-bucket-name"),
            ("DatasetsBucketArn", "datasets-bucket-arn"),
            ("ModelsBucketName", "models-bucket-name"),
            ("ModelsBucketArn", "models-bucket-arn"),
            ("CheckpointsBucketName", "checkpoints-bucket-name"),
            ("CheckpointsBucketArn", "checkpoints-bucket-arn"),
            # DatabaseStack (使用显式 export_name，但验证函数行为)
            ("ClusterEndpoint", "cluster-endpoint"),
            ("ReaderEndpoint", "reader-endpoint"),
            ("Port", "port"),
            ("SecretArn", "secret-arn"),
            ("ProxyEndpoint", "proxy-endpoint"),
            # FsxStack (使用显式 export_name，但验证函数行为)
            ("FileSystemId", "file-system-id"),
            ("FileSystemDnsName", "file-system-dns-name"),
            ("FileSystemMountName", "file-system-mount-name"),
            ("StorageCapacityGiB", "storage-capacity-gib"),
            ("TotalThroughputMBps", "total-throughput-mbps"),
        ],
    )
    def test_output_id_conversion(self, output_id: str, expected: str) -> None:
        """验证 output_id 到 kebab-case 的转换结果."""
        assert to_kebab_case(output_id) == expected
