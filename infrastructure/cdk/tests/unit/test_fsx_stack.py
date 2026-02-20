"""
FSx for Lustre Stack 单元测试.

测试覆盖:
- FSx 文件系统创建
- 存储容量配置
- 吞吐量层级选择
- 安全组配置
- 标签
- 各环境存储容量差异
"""

import aws_cdk as cdk
import pytest
from aws_cdk import aws_kms as kms
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import FsxLustreStack, NetworkStack, StorageStack

# =============================================================================
# 共用 Fixtures - 消除 4 处重复的依赖链创建
# =============================================================================


@pytest.fixture
def storage_stack(
    cdk_app: cdk.App,
    dev_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
    test_kms_key: kms.Key,
) -> StorageStack:
    """创建 Storage Stack 依赖."""
    return StorageStack(
        cdk_app,
        "TestStorageStack",
        env_config=dev_config,
        encryption_key=test_kms_key,
        env=cdk_env,
    )


@pytest.fixture
def fsx_stack(
    cdk_app: cdk.App,
    dev_config: EnvironmentConfig,
    cdk_env: cdk.Environment,
    network_stack: NetworkStack,
    storage_stack: StorageStack,
) -> FsxLustreStack:
    """创建 FSx Stack."""
    return FsxLustreStack(
        cdk_app,
        "TestFsxStack",
        env_config=dev_config,
        vpc=network_stack.vpc,
        datasets_bucket=storage_stack.datasets_bucket,
        env=cdk_env,
    )


@pytest.fixture
def template(fsx_stack: FsxLustreStack) -> Template:
    """获取 CloudFormation 模板."""
    return Template.from_stack(fsx_stack)


# =============================================================================
# 测试类
# =============================================================================


class TestFsxStackCreation:
    """FSx Stack 创建测试."""

    def test_stack_synthesizes(self, fsx_stack: FsxLustreStack) -> None:
        """验证 Stack 可以成功合成."""
        assert fsx_stack is not None

    def test_fsx_filesystem_created(self, template: Template) -> None:
        """验证 FSx 文件系统创建."""
        template.resource_count_is("AWS::FSx::FileSystem", 1)


class TestFsxConfiguration:
    """FSx 文件系统配置测试."""

    def test_lustre_filesystem_type(self, template: Template) -> None:
        """验证 Lustre 文件系统类型."""
        template.has_resource_properties(
            "AWS::FSx::FileSystem",
            {"FileSystemType": "LUSTRE"},
        )

    def test_storage_capacity(self, template: Template) -> None:
        """验证存储容量配置."""
        template.has_resource_properties(
            "AWS::FSx::FileSystem",
            {"StorageCapacity": Match.any_value()},
        )


class TestFsxSecurityGroup:
    """FSx 安全组配置测试."""

    def test_security_group_created(self, template: Template) -> None:
        """验证安全组创建."""
        template.resource_count_is("AWS::EC2::SecurityGroup", 1)

    def test_lustre_ports_allowed(self, template: Template) -> None:
        """验证 Lustre 端口 (988) 允许入站."""
        template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "SecurityGroupIngress": Match.array_with(
                    [
                        Match.object_like(
                            {"FromPort": 988, "ToPort": 988, "IpProtocol": "tcp"}
                        )
                    ]
                ),
            },
        )


class TestFsxTags:
    """FSx 标签测试."""

    def test_fsx_has_tags(self, template: Template) -> None:
        """验证 FSx 文件系统有标签."""
        filesystems = template.find_resources("AWS::FSx::FileSystem")
        assert len(filesystems) == 1, "Expected exactly 1 FSx filesystem"

        fs_props = list(filesystems.values())[0].get("Properties", {})
        tags = fs_props.get("Tags", [])
        assert len(tags) >= 1, "FSx filesystem should have at least 1 tag"


class TestEnvironmentSpecificConfiguration:
    """各环境 FSx 存储容量配置测试."""

    def _create_fsx_template(
        self,
        cdk_app: cdk.App,
        env_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        prefix: str,
    ) -> Template:
        """辅助方法: 创建指定环境的 FSx 模板."""
        network = NetworkStack(
            cdk_app, f"{prefix}Network", env_config=env_config, env=cdk_env
        )
        kms_stack = cdk.Stack(cdk_app, f"{prefix}Kms", env=cdk_env)
        test_key = kms.Key(kms_stack, "TestKey")
        storage = StorageStack(
            cdk_app,
            f"{prefix}Storage",
            env_config=env_config,
            encryption_key=test_key,
            env=cdk_env,
        )
        fsx = FsxLustreStack(
            cdk_app,
            f"{prefix}Fsx",
            env_config=env_config,
            vpc=network.vpc,
            datasets_bucket=storage.datasets_bucket,
            env=cdk_env,
        )
        return Template.from_stack(fsx)

    def _get_storage_capacity(self, template: Template) -> int:
        """辅助方法: 从模板中提取存储容量."""
        filesystems = template.find_resources("AWS::FSx::FileSystem")
        assert len(filesystems) == 1
        return (
            list(filesystems.values())[0]
            .get("Properties", {})
            .get("StorageCapacity", 0)
        )

    def test_dev_storage_capacity(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """验证开发环境存储容量 (>= 1.2 TiB 最小值)."""
        template = self._create_fsx_template(cdk_app, dev_config, cdk_env, "DevCap")
        capacity = self._get_storage_capacity(template)
        assert capacity >= 1200, f"Dev storage capacity {capacity} < 1200"

    def test_prod_storage_capacity(
        self, cdk_app: cdk.App, prod_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """验证生产环境存储容量 (>= 20 TiB)."""
        template = self._create_fsx_template(cdk_app, prod_config, cdk_env, "ProdCap")
        capacity = self._get_storage_capacity(template)
        assert capacity >= 20480, f"Prod storage capacity {capacity} < 20480"
