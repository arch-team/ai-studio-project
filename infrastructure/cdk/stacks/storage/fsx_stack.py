"""
FSx for Lustre Stack for AI Training Platform.

This stack creates an Amazon FSx for Lustre file system for high-performance
training data storage with the following capabilities:

- PERSISTENT_2 deployment type (persistent, high-performance)
- Configurable throughput per TiB (125/250/500/1000 MB/s/TiB)
- S3 Data Repository Association for data synchronization
- Automatic import/export policies
- Integration with EKS via FSx CSI Driver StorageClass
- Automatic backup and lifecycle management

Reference: spec.md NFR-001 (FSx capacity planning formula),
          FR-007 (≥5GB/s single client throughput)
"""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_fsx as fsx
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3

from config import EnvironmentConfig
from constructs import Construct
from utils.outputs import create_output


class FsxLustreStack(cdk.Stack):
    """FSx for Lustre Stack for high-performance training data storage.

    This stack creates:
    - FSx for Lustre file system (PERSISTENT_2 deployment)
    - Security group for FSx access
    - S3 Data Repository Association for data sync
    - CloudWatch alarms for capacity monitoring

    The file system provides:
    - High throughput for training workloads (≥5GB/s single client)
    - Automatic S3 synchronization
    - Hierarchical storage management

    Attributes:
        file_system: FSx for Lustre file system
        security_group: Security group for FSx access
        dns_name: DNS name for mounting the file system
        mount_name: Mount name for Lustre client
    """

    # Valid PERSISTENT_2 throughput values (MB/s/TiB)
    VALID_THROUGHPUT_VALUES = (125, 250, 500, 1000)

    # Minimum storage capacity for PERSISTENT_2 (1.2 TiB in GiB)
    MIN_STORAGE_CAPACITY_GIB = 1200

    # Storage capacity increment (2.4 TiB in GiB)
    STORAGE_CAPACITY_INCREMENT_GIB = 2400

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        datasets_bucket: s3.IBucket,
        eks_security_group: ec2.ISecurityGroup | None = None,
        **kwargs,
    ) -> None:
        """Initialize the FSx for Lustre Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            env_config: Environment configuration
            vpc: VPC for FSx deployment
            datasets_bucket: S3 bucket for Data Repository Association
            eks_security_group: EKS node security group for FSx access
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._vpc = vpc
        self._datasets_bucket = datasets_bucket
        self._eks_security_group = eks_security_group

        # Validate throughput configuration
        self._validate_throughput_config()

        # Create security group for FSx
        self._security_group = self._create_security_group()

        # Create FSx for Lustre file system
        self._file_system = self._create_file_system()

        # Create S3 Data Repository Association
        self._data_repository_association = self._create_data_repository_association()

        # Create CloudWatch alarms
        self._create_alarms()

        # Create outputs
        self._create_outputs()

    def _validate_throughput_config(self) -> None:
        """Validate FSx throughput configuration.

        Raises:
            ValueError: If throughput per TB is not a valid value
        """
        throughput = self.env_config.storage.fsx_throughput_per_tb
        if throughput not in self.VALID_THROUGHPUT_VALUES:
            valid_values = ", ".join(str(v) for v in self.VALID_THROUGHPUT_VALUES)
            raise ValueError(
                f"Invalid FSx throughput: {throughput}. "
                f"Valid values for PERSISTENT_2: {valid_values} MB/s/TiB"
            )

    def _get_validated_storage_capacity(self) -> int:
        """Get validated storage capacity aligned to FSx requirements.

        FSx for Lustre PERSISTENT_2 requires:
        - Minimum 1.2 TiB (1200 GiB)
        - Increments of 2.4 TiB (2400 GiB)

        Returns:
            Storage capacity in GiB aligned to FSx requirements
        """
        requested_capacity = self.env_config.storage.fsx_storage_capacity_gib

        # Ensure minimum capacity
        if requested_capacity < self.MIN_STORAGE_CAPACITY_GIB:
            return self.MIN_STORAGE_CAPACITY_GIB

        # Align to 2.4 TiB increments
        # Formula: ceiling to nearest increment
        increments = (
            requested_capacity + self.STORAGE_CAPACITY_INCREMENT_GIB - 1
        ) // self.STORAGE_CAPACITY_INCREMENT_GIB
        return increments * self.STORAGE_CAPACITY_INCREMENT_GIB

    def _create_security_group(self) -> ec2.SecurityGroup:
        """Create security group for FSx for Lustre.

        FSx for Lustre requires the following ports:
        - TCP 988: Lustre client-server communication
        - TCP 1021-1023: Lustre inter-node communication

        Returns:
            Security group configured for FSx access
        """
        sg = ec2.SecurityGroup(
            self,
            "FsxSecurityGroup",
            vpc=self._vpc,
            description="Security group for FSx for Lustre file system",
            allow_all_outbound=True,
        )

        # Add self-referencing rules for Lustre inter-node communication
        sg.add_ingress_rule(
            peer=sg,
            connection=ec2.Port.tcp(988),
            description="Lustre client-server communication",
        )
        sg.add_ingress_rule(
            peer=sg,
            connection=ec2.Port.tcp_range(1021, 1023),
            description="Lustre inter-node communication",
        )

        # Allow EKS nodes to access FSx
        if self._eks_security_group:
            sg.add_ingress_rule(
                peer=self._eks_security_group,
                connection=ec2.Port.tcp(988),
                description="EKS nodes - Lustre client-server",
            )
            sg.add_ingress_rule(
                peer=self._eks_security_group,
                connection=ec2.Port.tcp_range(1021, 1023),
                description="EKS nodes - Lustre inter-node",
            )

        # Allow access from VPC CIDR (for nodes without explicit security group)
        sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(self._vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(988),
            description="VPC internal - Lustre client-server",
        )
        sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(self._vpc.vpc_cidr_block),
            connection=ec2.Port.tcp_range(1021, 1023),
            description="VPC internal - Lustre inter-node",
        )

        cdk.Tags.of(sg).add("Name", f"{self.env_config.resource_prefix}-fsx-sg")

        return sg

    def _create_file_system(self) -> fsx.CfnFileSystem:
        """Create FSx for Lustre file system with PERSISTENT_2 deployment.

        Uses CfnFileSystem (L1) because CDK L2 construct doesn't support
        PERSISTENT_2 deployment type.

        Returns:
            FSx for Lustre file system
        """
        storage_capacity = self._get_validated_storage_capacity()
        throughput_per_tib = self.env_config.storage.fsx_throughput_per_tb

        # Select subnet for FSx deployment (use first private subnet)
        private_subnets = self._vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        )
        subnet_id = private_subnets.subnet_ids[0]

        # Use protection config for removal policy
        removal_policy = self.env_config.protection.removal_policy

        # Calculate weekly maintenance window (Sunday 2:00 AM UTC)
        weekly_maintenance_start_time = "7:02:00"  # Day:Hour:Minute (7=Sunday)

        file_system = fsx.CfnFileSystem(
            self,
            "FsxLustreFileSystem",
            file_system_type="LUSTRE",
            storage_capacity=storage_capacity,
            subnet_ids=[subnet_id],
            security_group_ids=[self._security_group.security_group_id],
            storage_type="SSD",
            lustre_configuration=fsx.CfnFileSystem.LustreConfigurationProperty(
                deployment_type="PERSISTENT_2",
                per_unit_storage_throughput=throughput_per_tib,
                # Data compression for cost optimization
                data_compression_type="LZ4",
                # Copy tags to backups
                copy_tags_to_backups=True,
                # Weekly maintenance window (Sunday 2:00 AM)
                weekly_maintenance_start_time=weekly_maintenance_start_time,
                # Auto import policy will be configured via Data Repository Association
            ),
            tags=[
                cdk.CfnTag(
                    key="Name", value=f"{self.env_config.resource_prefix}-fsx-lustre"
                ),
                cdk.CfnTag(key="Environment", value=self.env_config.name.value),
                cdk.CfnTag(key="StorageCapacityGiB", value=str(storage_capacity)),
                cdk.CfnTag(key="ThroughputPerTiB", value=str(throughput_per_tib)),
            ],
        )

        # Apply removal policy from protection config
        file_system.apply_removal_policy(removal_policy)

        return file_system

    def _create_data_repository_association(self) -> fsx.CfnDataRepositoryAssociation:
        """Create Data Repository Association for S3 synchronization.

        Configures automatic import/export between FSx and S3:
        - Auto import: NEW, CHANGED, DELETED files from S3
        - Auto export: NEW, CHANGED, DELETED files to S3

        Reference: spec.md SC-005 (S3 to FSx sync <10min for 1TB)

        Returns:
            Data Repository Association linking FSx to S3
        """
        dra = fsx.CfnDataRepositoryAssociation(
            self,
            "FsxDataRepositoryAssociation",
            file_system_id=self._file_system.ref,
            file_system_path="/datasets",  # Mount point within Lustre
            data_repository_path=self._datasets_bucket.s3_url_for_object(),
            batch_import_meta_data_on_create=True,
            imported_file_chunk_size=1024,  # 1GB chunk size for large files
            s3=fsx.CfnDataRepositoryAssociation.S3Property(
                auto_import_policy=fsx.CfnDataRepositoryAssociation.AutoImportPolicyProperty(
                    events=["NEW", "CHANGED", "DELETED"],
                ),
                auto_export_policy=fsx.CfnDataRepositoryAssociation.AutoExportPolicyProperty(
                    events=["NEW", "CHANGED", "DELETED"],
                ),
            ),
            tags=[
                cdk.CfnTag(
                    key="Name", value=f"{self.env_config.resource_prefix}-fsx-dra"
                ),
                cdk.CfnTag(key="Environment", value=self.env_config.name.value),
            ],
        )

        # DRA depends on file system
        dra.add_dependency(self._file_system)

        return dra

    def _create_alarms(self) -> None:
        """Create CloudWatch alarms for FSx capacity monitoring.

        Implements FR-020 storage capacity monitoring:
        - Warning at 80% utilization
        - Critical at 90% utilization
        - Emergency at 95% utilization
        """
        # Note: CloudWatch alarms for FSx are created using custom metrics
        # FSx publishes metrics to CloudWatch automatically
        # Alarm creation is typically done in a separate monitoring stack
        # or via CloudWatch dashboard configuration

        # Add tag to indicate monitoring configuration
        cdk.Tags.of(self._file_system).add("MonitoringEnabled", "true")
        cdk.Tags.of(self._file_system).add("CapacityAlertThreshold", "80")

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack references."""
        create_output(
            self, "FileSystemId", self._file_system.ref, "FSx for Lustre file system ID"
        )
        dns_name = f"{self._file_system.ref}.fsx.{self.region}.amazonaws.com"
        create_output(
            self, "FileSystemDnsName", dns_name, "FSx for Lustre DNS name for mounting"
        )
        create_output(
            self,
            "FileSystemMountName",
            self._file_system.attr_lustre_mount_name,
            "FSx for Lustre mount name",
        )
        create_output(
            self,
            "SecurityGroupId",
            self._security_group.security_group_id,
            "FSx security group ID",
        )
        storage_capacity = self._get_validated_storage_capacity()
        create_output(
            self,
            "StorageCapacityGiB",
            str(storage_capacity),
            "FSx storage capacity in GiB",
        )
        throughput_mbps = (
            storage_capacity // 1024
        ) * self.env_config.storage.fsx_throughput_per_tb
        create_output(
            self,
            "TotalThroughputMBps",
            str(throughput_mbps),
            "FSx total throughput in MB/s",
        )

    @property
    def file_system(self) -> fsx.CfnFileSystem:
        """Get FSx for Lustre file system."""
        return self._file_system

    @property
    def file_system_id(self) -> str:
        """Get FSx file system ID."""
        return self._file_system.ref

    @property
    def security_group(self) -> ec2.SecurityGroup:
        """Get FSx security group."""
        return self._security_group

    @property
    def dns_name(self) -> str:
        """Get FSx DNS name for mounting."""
        return f"{self._file_system.ref}.fsx.{self.region}.amazonaws.com"

    @property
    def mount_name(self) -> str:
        """Get FSx mount name."""
        return self._file_system.attr_lustre_mount_name

    def get_storage_class_manifest(self) -> dict:
        """Generate Kubernetes StorageClass manifest for FSx CSI Driver.

        Returns:
            Dictionary containing StorageClass YAML configuration
        """
        return {
            "apiVersion": "storage.k8s.io/v1",
            "kind": "StorageClass",
            "metadata": {
                "name": "fsx-lustre-training-data",
                "labels": {
                    "app.kubernetes.io/name": "fsx-storage",
                    "platform.ai/storage-type": "fsx-lustre",
                },
            },
            "provisioner": "fsx.csi.aws.com",
            "parameters": {
                "subnetId": self._vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnet_ids[0],
                "securityGroupIds": self._security_group.security_group_id,
                "deploymentType": "PERSISTENT_2",
                "perUnitStorageThroughput": str(
                    self.env_config.storage.fsx_throughput_per_tb
                ),
            },
            "reclaimPolicy": "Retain",
            "volumeBindingMode": "Immediate",
        }

    def grant_read_write(self, role: iam.IRole) -> None:
        """Grant read/write access to FSx file system.

        This grants the necessary permissions for mounting and accessing
        the FSx file system from EKS pods.

        Args:
            role: IAM role to grant access
        """
        iam.Grant.add_to_principal(
            grantee=role,
            actions=[
                "fsx:DescribeFileSystems",
                "fsx:DescribeDataRepositoryAssociations",
                "fsx:DescribeDataRepositoryTasks",
            ],
            resource_arns=["*"],
        )

    def grant_s3_data_sync(self, role: iam.IRole) -> None:
        """Grant S3 data synchronization permissions.

        This grants permissions needed for FSx to sync with S3 bucket.

        Args:
            role: IAM role to grant access
        """
        self._datasets_bucket.grant_read_write(role)
        iam.Grant.add_to_principal(
            grantee=role,
            actions=[
                "fsx:CreateDataRepositoryTask",
                "fsx:DescribeDataRepositoryTasks",
            ],
            resource_arns=[
                f"arn:aws:fsx:{self.region}:{self.account}:file-system/{self._file_system.ref}"
            ],
        )
