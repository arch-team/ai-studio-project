"""FSx for Lustre Stack — 高性能训练数据存储。

PERSISTENT_2 部署，支持 S3 数据仓库关联自动同步。
参考: spec.md NFR-001 (FSx 容量规划), FR-007 (≥5GB/s 单客户端吞吐)
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_fsx as fsx
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3

from config import EnvironmentConfig
from constructs import Construct
from utils.outputs import create_output
from utils.tagging import create_cfn_tags


class FsxLustreStack(cdk.Stack):
    """FSx for Lustre Stack — 高性能训练数据存储。"""

    # PERSISTENT_2 有效吞吐量值 (MB/s/TiB)
    VALID_THROUGHPUT_VALUES = (125, 250, 500, 1000)

    # PERSISTENT_2 最小存储容量 (1.2 TiB = 1200 GiB)
    MIN_STORAGE_CAPACITY_GIB = 1200

    # 存储容量增量 (2.4 TiB = 2400 GiB)
    STORAGE_CAPACITY_INCREMENT_GIB = 2400

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        datasets_bucket: s3.IBucket,
        eks_security_group: ec2.ISecurityGroup | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._vpc = vpc
        self._datasets_bucket = datasets_bucket
        self._eks_security_group = eks_security_group

        self._validate_throughput_config()
        self._security_group = self._create_security_group()
        self._file_system = self._create_file_system()
        self._data_repository_association = self._create_data_repository_association()
        self._create_alarms()
        self._create_outputs()

    def _validate_throughput_config(self) -> None:
        """验证 FSx 吞吐量配置。

        Raises:
            ValueError: 吞吐量不在 VALID_THROUGHPUT_VALUES 范围内时
        """
        throughput = self.env_config.storage.fsx_throughput_per_tb
        if throughput not in self.VALID_THROUGHPUT_VALUES:
            valid_values = ", ".join(str(v) for v in self.VALID_THROUGHPUT_VALUES)
            raise ValueError(
                f"Invalid FSx throughput: {throughput}. "
                f"Valid values for PERSISTENT_2: {valid_values} MB/s/TiB"
            )

    def _get_validated_storage_capacity(self) -> int:
        """获取对齐到 FSx PERSISTENT_2 要求的存储容量 (最小 1.2 TiB, 增量 2.4 TiB)。"""
        requested_capacity = self.env_config.storage.fsx_storage_capacity_gib

        if requested_capacity < self.MIN_STORAGE_CAPACITY_GIB:
            return self.MIN_STORAGE_CAPACITY_GIB

        # 向上对齐到 2.4 TiB 增量
        increments = (
            requested_capacity + self.STORAGE_CAPACITY_INCREMENT_GIB - 1
        ) // self.STORAGE_CAPACITY_INCREMENT_GIB
        return increments * self.STORAGE_CAPACITY_INCREMENT_GIB

    @staticmethod
    def _add_lustre_ingress_rules(
        sg: ec2.SecurityGroup,
        peer: ec2.IPeer,
        description_prefix: str,
    ) -> None:
        """为指定 peer 添加 Lustre 所需端口的入站规则。

        FSx for Lustre 需要:
        - TCP 988: Lustre client-server 通信
        - TCP 1021-1023: Lustre 节点间通信

        Args:
            sg: 安全组
            peer: 入站规则的来源 peer
            description_prefix: 规则描述的前缀
        """
        sg.add_ingress_rule(
            peer=peer,
            connection=ec2.Port.tcp(988),
            description=f"{description_prefix} - Lustre client-server",
        )
        sg.add_ingress_rule(
            peer=peer,
            connection=ec2.Port.tcp_range(1021, 1023),
            description=f"{description_prefix} - Lustre inter-node",
        )

    def _create_security_group(self) -> ec2.SecurityGroup:
        """创建 FSx 安全组，允许 Lustre 通信端口 (TCP 988, 1021-1023)。"""
        sg = ec2.SecurityGroup(
            self,
            "FsxSecurityGroup",
            vpc=self._vpc,
            description="Security group for FSx for Lustre file system",
            allow_all_outbound=True,
        )

        # 自引用规则: Lustre 节点间通信
        self._add_lustre_ingress_rules(sg, sg, "Self-reference")

        # 允许 EKS 节点访问 FSx
        if self._eks_security_group:
            self._add_lustre_ingress_rules(sg, self._eks_security_group, "EKS nodes")

        # 仅允许 Private 子网访问 (收窄原 VPC CIDR 全范围规则)
        for subnet in self._vpc.private_subnets:
            self._add_lustre_ingress_rules(
                sg,
                ec2.Peer.ipv4(subnet.ipv4_cidr_block),
                f"Subnet {subnet.node.id}",
            )

        cdk.Tags.of(sg).add("Name", f"{self.env_config.resource_prefix}-fsx-sg")

        return sg

    def _create_file_system(self) -> fsx.CfnFileSystem:
        """创建 FSx for Lustre 文件系统 (PERSISTENT_2)。

        使用 L1 CfnFileSystem 因为 CDK L2 不支持 PERSISTENT_2 部署类型。
        """
        storage_capacity = self._get_validated_storage_capacity()
        throughput_per_tib = self.env_config.storage.fsx_throughput_per_tb

        private_subnets = self._vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        )
        subnet_id = private_subnets.subnet_ids[0]

        removal_policy = self.env_config.protection.removal_policy

        # Day:Hour:Minute (7=Sunday, 02:00 UTC)
        weekly_maintenance_start_time = "7:02:00"

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
                data_compression_type="LZ4",
                copy_tags_to_backups=True,
                weekly_maintenance_start_time=weekly_maintenance_start_time,
            ),
            tags=create_cfn_tags(
                self.env_config,
                "fsx-lustre",
                additional_tags={
                    "StorageCapacityGiB": str(storage_capacity),
                    "ThroughputPerTiB": str(throughput_per_tib),
                },
            ),
        )

        file_system.apply_removal_policy(removal_policy)

        return file_system

    def _create_data_repository_association(self) -> fsx.CfnDataRepositoryAssociation:
        """创建 S3 数据仓库关联，配置双向自动同步 (NEW/CHANGED/DELETED)。

        参考: spec.md SC-005 (S3 → FSx 同步 <10min/1TB)
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
            tags=create_cfn_tags(self.env_config, "fsx-dra"),
        )

        dra.add_dependency(self._file_system)

        return dra

    def _create_alarms(self) -> None:
        """创建 CloudWatch 容量监控告警 (FR-020: 80%/90%/95% 阈值)。

        FSx 自动向 CloudWatch 发布指标，具体告警在监控 Stack 中配置。
        """
        cdk.Tags.of(self._file_system).add("MonitoringEnabled", "true")
        cdk.Tags.of(self._file_system).add("CapacityAlertThreshold", "80")

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出。"""
        prefix = self.env_config.resource_prefix
        storage_capacity = self._get_validated_storage_capacity()
        throughput_mbps = (
            storage_capacity // 1024
        ) * self.env_config.storage.fsx_throughput_per_tb

        # (output_id, value, description, export_name)
        outputs = [
            ("FileSystemId", self._file_system.ref, "FSx for Lustre file system ID", f"{prefix}-fsx-id"),
            (
                "FileSystemDnsName",
                self.dns_name,
                "FSx for Lustre DNS name for mounting",
                f"{prefix}-fsx-dns",
            ),
            (
                "FileSystemMountName",
                self._file_system.attr_lustre_mount_name,
                "FSx for Lustre mount name",
                f"{prefix}-fsx-mount",
            ),
            (
                "SecurityGroupId",
                self._security_group.security_group_id,
                "FSx security group ID",
                f"{prefix}-fsx-sg-id",
            ),
            (
                "StorageCapacityGiB",
                str(storage_capacity),
                "FSx storage capacity in GiB",
                f"{prefix}-fsx-capacity",
            ),
            (
                "TotalThroughputMBps",
                str(throughput_mbps),
                "FSx total throughput in MB/s",
                f"{prefix}-fsx-throughput",
            ),
        ]
        for output_id, value, description, export_name in outputs:
            create_output(self, output_id, value, description, export_name=export_name)

    @property
    def file_system(self) -> fsx.CfnFileSystem:
        return self._file_system

    @property
    def file_system_id(self) -> str:
        return self._file_system.ref

    @property
    def security_group(self) -> ec2.SecurityGroup:
        return self._security_group

    @property
    def dns_name(self) -> str:
        return f"{self._file_system.ref}.fsx.{self.region}.amazonaws.com"

    @property
    def mount_name(self) -> str:
        return self._file_system.attr_lustre_mount_name

    def get_storage_class_manifest(self) -> dict:
        """生成 FSx CSI Driver 的 Kubernetes StorageClass 配置。"""
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
        """授予 FSx 文件系统读写权限 (用于 EKS Pod 挂载)。"""
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
        """授予 S3 数据同步权限 (FSx ↔ S3 bucket)。"""
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
