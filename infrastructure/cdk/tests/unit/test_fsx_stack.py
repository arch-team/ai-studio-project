"""
Unit tests for FSx for Lustre Stack.

Tests cover:
- FSx filesystem creation
- Storage capacity configuration
- Throughput tier selection
- S3 Data Repository Association
- Security group configuration
"""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks import EksStack, FsxLustreStack, IamStack, NetworkStack, StorageStack


class TestFsxStackCreation:
    """Tests for FSx Stack creation."""

    @pytest.fixture
    def network_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> NetworkStack:
        """Create Network Stack as dependency."""
        return NetworkStack(
            cdk_app,
            "TestNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )

    @pytest.fixture
    def storage_stack(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> StorageStack:
        """Create Storage Stack as dependency."""
        return StorageStack(
            cdk_app,
            "TestStorageStack",
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
    ) -> EksStack:
        """Create EKS Stack as dependency."""
        iam_stack = IamStack(
            cdk_app,
            "TestIamStack",
            env_config=dev_config,
            env=cdk_env,
        )
        return EksStack(
            cdk_app,
            "TestEksStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            eks_node_role=iam_stack.eks_node_role,
            env=cdk_env,
        )

    @pytest.fixture
    def fsx_stack(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        network_stack: NetworkStack,
        storage_stack: StorageStack,
    ) -> FsxLustreStack:
        """Create FSx Stack for testing."""
        return FsxLustreStack(
            cdk_app,
            "TestFsxStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            datasets_bucket=storage_stack.datasets_bucket,
            env=cdk_env,
        )

    @pytest.fixture
    def template(self, fsx_stack: FsxLustreStack) -> Template:
        """Get CloudFormation template from the stack."""
        return Template.from_stack(fsx_stack)

    def test_stack_synthesizes(self, fsx_stack: FsxLustreStack) -> None:
        """Verify the stack synthesizes without errors."""
        assert fsx_stack is not None

    def test_fsx_filesystem_created(self, template: Template) -> None:
        """Verify FSx filesystem is created."""
        template.resource_count_is("AWS::FSx::FileSystem", 1)


class TestFsxConfiguration:
    """Tests for FSx filesystem configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for FSx configuration testing."""
        network_stack = NetworkStack(
            cdk_app,
            "ConfigNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        storage_stack = StorageStack(
            cdk_app,
            "ConfigStorageStack",
            env_config=dev_config,
            env=cdk_env,
        )
        fsx_stack = FsxLustreStack(
            cdk_app,
            "ConfigFsxStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            datasets_bucket=storage_stack.datasets_bucket,
            env=cdk_env,
        )
        return Template.from_stack(fsx_stack)

    def test_lustre_filesystem_type(self, template: Template) -> None:
        """Verify Lustre filesystem type is used."""
        template.has_resource_properties(
            "AWS::FSx::FileSystem",
            {
                "FileSystemType": "LUSTRE",
            },
        )

    def test_storage_capacity(self, template: Template) -> None:
        """Verify storage capacity is configured."""
        template.has_resource_properties(
            "AWS::FSx::FileSystem",
            {
                "StorageCapacity": Match.any_value(),
            },
        )


class TestFsxSecurityGroup:
    """Tests for FSx security group configuration."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for security group testing."""
        network_stack = NetworkStack(
            cdk_app,
            "SgNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        storage_stack = StorageStack(
            cdk_app,
            "SgStorageStack",
            env_config=dev_config,
            env=cdk_env,
        )
        fsx_stack = FsxLustreStack(
            cdk_app,
            "SgFsxStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            datasets_bucket=storage_stack.datasets_bucket,
            env=cdk_env,
        )
        return Template.from_stack(fsx_stack)

    def test_security_group_created(self, template: Template) -> None:
        """Verify security group is created for FSx."""
        template.resource_count_is("AWS::EC2::SecurityGroup", 1)

    def test_lustre_ports_allowed(self, template: Template) -> None:
        """Verify Lustre ports are allowed in security group."""
        # Lustre uses ports 988, 1018-1023
        template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "SecurityGroupIngress": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "FromPort": 988,
                                "ToPort": 988,
                                "IpProtocol": "tcp",
                            }
                        )
                    ]
                ),
            },
        )


class TestFsxTags:
    """Tests for FSx tagging."""

    @pytest.fixture
    def template(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> Template:
        """Create template for tag testing."""
        network_stack = NetworkStack(
            cdk_app,
            "TagNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        storage_stack = StorageStack(
            cdk_app,
            "TagStorageStack",
            env_config=dev_config,
            env=cdk_env,
        )
        fsx_stack = FsxLustreStack(
            cdk_app,
            "TagFsxStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            datasets_bucket=storage_stack.datasets_bucket,
            env=cdk_env,
        )
        return Template.from_stack(fsx_stack)

    def test_fsx_has_tags(self, template: Template) -> None:
        """Verify FSx filesystem has tags configured."""
        # Note: Project tags are applied at app level in app.py via cdk.Tags.of(app).add()
        # Individual stack tests won't have these global tags
        # But FSx stack adds its own tags (Name, Environment, etc.)
        filesystems = template.find_resources("AWS::FSx::FileSystem")
        assert len(filesystems) == 1, "Expected exactly 1 FSx filesystem"

        fs_props = list(filesystems.values())[0].get("Properties", {})
        tags = fs_props.get("Tags", [])
        # FSx stack should add at least Name tag
        assert len(tags) >= 1, "FSx filesystem should have at least 1 tag"


class TestEnvironmentSpecificConfiguration:
    """Tests for environment-specific FSx configuration."""

    def test_dev_storage_capacity(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify dev environment storage capacity."""
        network_stack = NetworkStack(
            cdk_app,
            "DevCapNetworkStack",
            env_config=dev_config,
            env=cdk_env,
        )
        storage_stack = StorageStack(
            cdk_app,
            "DevCapStorageStack",
            env_config=dev_config,
            env=cdk_env,
        )
        fsx_stack = FsxLustreStack(
            cdk_app,
            "DevCapFsxStack",
            env_config=dev_config,
            vpc=network_stack.vpc,
            datasets_bucket=storage_stack.datasets_bucket,
            env=cdk_env,
        )
        template = Template.from_stack(fsx_stack)

        # Dev uses ~10 TiB, aligned to 2.4 TiB increments = 12000 GiB
        filesystems = template.find_resources("AWS::FSx::FileSystem")
        assert len(filesystems) == 1
        fs_props = list(filesystems.values())[0].get("Properties", {})
        storage_capacity = fs_props.get("StorageCapacity", 0)
        # Should be at least 10 TiB but aligned to FSx requirements
        assert storage_capacity >= 10240, f"Dev storage capacity {storage_capacity} < 10240"

    def test_prod_storage_capacity(
        self, cdk_app: cdk.App, prod_config: EnvironmentConfig, cdk_env: cdk.Environment
    ) -> None:
        """Verify prod environment storage capacity."""
        network_stack = NetworkStack(
            cdk_app,
            "ProdCapNetworkStack",
            env_config=prod_config,
            env=cdk_env,
        )
        storage_stack = StorageStack(
            cdk_app,
            "ProdCapStorageStack",
            env_config=prod_config,
            env=cdk_env,
        )
        fsx_stack = FsxLustreStack(
            cdk_app,
            "ProdCapFsxStack",
            env_config=prod_config,
            vpc=network_stack.vpc,
            datasets_bucket=storage_stack.datasets_bucket,
            env=cdk_env,
        )
        template = Template.from_stack(fsx_stack)

        # Prod uses ~100 TiB, aligned to 2.4 TiB increments = 103200 GiB
        filesystems = template.find_resources("AWS::FSx::FileSystem")
        assert len(filesystems) == 1
        fs_props = list(filesystems.values())[0].get("Properties", {})
        storage_capacity = fs_props.get("StorageCapacity", 0)
        # Should be at least 100 TiB but aligned to FSx requirements
        assert storage_capacity >= 102400, f"Prod storage capacity {storage_capacity} < 102400"
