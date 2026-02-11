"""
Database Stack for AI Training Platform.

This stack creates Aurora MySQL Serverless v2 with:
- Auto-scaling capacity (0.5 - 16 ACU)
- Multi-AZ deployment for high availability
- RDS Proxy for connection pooling
- Automated backups with point-in-time recovery
- Encryption at rest using AWS managed keys
"""

import aws_cdk as cdk
from aws_cdk import Duration
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_kms as kms
from aws_cdk import aws_logs as logs
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager

from config import EnvironmentConfig
from config.environments import EnvironmentType
from constructs import Construct
from utils.outputs import create_output


class DatabaseStack(cdk.Stack):
    """Aurora MySQL Serverless v2 Stack with RDS Proxy.

    This stack creates:
    - Aurora MySQL Serverless v2 cluster
    - RDS Proxy for connection pooling (optional)
    - Security groups for database access
    - Secrets Manager secret for credentials
    - CloudWatch log group for audit logs

    Attributes:
        cluster: Aurora database cluster
        proxy: RDS Proxy instance (if enabled)
        security_group: Security group for database access
        secret: Secrets Manager secret containing credentials
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        storage_encryption_key: kms.IKey | None = None,
        **kwargs,
    ) -> None:
        # storage_encryption_key: 自定义 KMS Key 用于存储加密 (None 则使用 AWS managed key)
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._vpc = vpc
        self._storage_encryption_key = storage_encryption_key

        # Create security group for database access
        self._security_group = self._create_security_group()

        # Create subnet group for Aurora
        self._subnet_group = self._create_subnet_group()

        # Create parameter group with custom settings
        self._parameter_group = self._create_parameter_group()

        # Create Aurora Serverless v2 cluster
        self._cluster = self._create_aurora_cluster()

        # Create RDS Proxy if enabled
        self._proxy: rds.DatabaseProxy | None = None
        if env_config.database.enable_proxy:
            self._proxy = self._create_rds_proxy()

        # Export outputs
        self._create_outputs()

    def _create_security_group(self) -> ec2.SecurityGroup:
        """Create security group for Aurora database.

        Allows MySQL (3306) traffic from within VPC.
        """
        sg = ec2.SecurityGroup(
            self,
            "DatabaseSg",
            vpc=self._vpc,
            security_group_name=f"{self.env_config.resource_prefix}-aurora-sg",
            description="Security group for Aurora MySQL",
            allow_all_outbound=False,
        )

        # 仅允许 Private 子网访问 MySQL (收窄原 VPC CIDR 全范围规则)
        for subnet in self._vpc.private_subnets:
            sg.add_ingress_rule(
                peer=ec2.Peer.ipv4(subnet.ipv4_cidr_block),
                connection=ec2.Port.tcp(3306),
                description=f"MySQL from {subnet.node.id}",
            )

        cdk.Tags.of(sg).add("Name", f"{self.env_config.resource_prefix}-aurora-sg")

        return sg

    def _create_subnet_group(self) -> rds.SubnetGroup:
        """Create DB subnet group in private data subnets."""
        return rds.SubnetGroup(
            self,
            "SubnetGroup",
            vpc=self._vpc,
            subnet_group_name=f"{self.env_config.resource_prefix}-aurora-subnet-group",
            description="Subnet group for Aurora MySQL in private data layer",
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
        )

    def _create_parameter_group(self) -> rds.ParameterGroup:
        """创建数据库参数组，按功能分类配置。"""
        is_dev = self.env_config.name == EnvironmentType.DEV

        return rds.ParameterGroup(
            self,
            "ParameterGroup",
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=rds.AuroraMysqlEngineVersion.VER_3_04_0
            ),
            description="Parameter group for AI Training Platform Aurora MySQL",
            parameters={
                # 性能优化
                "innodb_buffer_pool_size": "{DBInstanceClassMemory*3/4}",
                "max_connections": "LEAST({DBInstanceClassMemory/9531392},5000)",
                # 字符集（UTF-8 支持）
                "character_set_server": "utf8mb4",
                "character_set_client": "utf8mb4",
                "collation_server": "utf8mb4_unicode_ci",
                # 查询日志（开发环境启用，生产环境禁用）
                "slow_query_log": "1" if is_dev else "0",
                "long_query_time": "2",
                # 时区
                "time_zone": "UTC",
            },
        )

    def _create_aurora_cluster(self) -> rds.DatabaseCluster:
        """Create Aurora MySQL Serverless v2 cluster.

        Features:
        - Serverless v2 with configurable ACU range
        - Multi-AZ deployment
        - Encryption at rest with AWS managed key
        - Automated backups with PITR
        - CloudWatch logs export
        """
        db_config = self.env_config.database

        # Create credentials secret
        credentials = rds.Credentials.from_generated_secret(
            username="admin",
            secret_name=f"{self.env_config.resource_prefix}/aurora/credentials",
        )

        # Create CloudWatch log group for audit logs
        # Log group is created but not assigned as Aurora will auto-create it
        # This explicit creation ensures proper lifecycle management
        # Note: LogGroup doesn't support SNAPSHOT policy, always use DESTROY
        logs.LogGroup(
            self,
            "AuditLogGroup",
            log_group_name=f"/aws/rds/{self.env_config.resource_prefix}/aurora/audit",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Create Aurora Serverless v2 cluster
        cluster = rds.DatabaseCluster(
            self,
            "AuroraCluster",
            cluster_identifier=f"{self.env_config.resource_prefix}-aurora",
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=rds.AuroraMysqlEngineVersion.VER_3_04_0
            ),
            credentials=credentials,
            default_database_name="ai_platform",
            # Serverless v2 configuration
            serverless_v2_min_capacity=db_config.min_acu,
            serverless_v2_max_capacity=db_config.max_acu,
            # Writer instance (Serverless v2)
            writer=rds.ClusterInstance.serverless_v2(
                "Writer",
                instance_identifier=f"{self.env_config.resource_prefix}-aurora-writer",
            ),
            # Reader instance for read scaling (Serverless v2)
            # Dev 环境不创建 Reader 以节省成本
            readers=(
                [
                    rds.ClusterInstance.serverless_v2(
                        "Reader",
                        instance_identifier=f"{self.env_config.resource_prefix}-aurora-reader",
                        scale_with_writer=True,
                    ),
                ]
                if self.env_config.name != EnvironmentType.DEV
                else []
            ),
            # Network configuration
            vpc=self._vpc,
            subnet_group=self._subnet_group,
            security_groups=[self._security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            # Backup configuration
            backup=rds.BackupProps(
                retention=Duration.days(db_config.backup_retention_days),
                preferred_window="03:00-04:00",  # UTC
            ),
            # Security configuration
            storage_encrypted=True,
            storage_encryption_key=self._storage_encryption_key,  # None = AWS managed key
            iam_authentication=True,  # Enable IAM DB authentication
            # Maintenance window
            preferred_maintenance_window="Sun:05:00-Sun:06:00",  # UTC
            # CloudWatch logs export
            cloudwatch_logs_exports=["audit", "error", "slowquery"],
            cloudwatch_logs_retention=logs.RetentionDays.ONE_MONTH,
            # Parameter group
            parameter_group=self._parameter_group,
            # Removal policy (from protection config)
            removal_policy=self.env_config.protection.removal_policy,
            # Deletion protection (from protection config)
            deletion_protection=self.env_config.protection.enable_deletion_protection,
        )

        # Store secret reference
        self._secret = cluster.secret

        return cluster

    def _create_rds_proxy(self) -> rds.DatabaseProxy:
        """Create RDS Proxy for connection pooling.

        Benefits:
        - Connection pooling reduces database load
        - Automatic failover for multi-AZ
        - IAM authentication support
        """
        proxy = rds.DatabaseProxy(
            self,
            "RdsProxy",
            db_proxy_name=f"{self.env_config.resource_prefix}-aurora-proxy",
            proxy_target=rds.ProxyTarget.from_cluster(self._cluster),
            vpc=self._vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            security_groups=[self._security_group],
            secrets=[self._cluster.secret],  # type: ignore
            require_tls=True,
            iam_auth=True,
            # Connection settings
            idle_client_timeout=Duration.minutes(30),
            max_connections_percent=100,
            max_idle_connections_percent=50,
            borrow_timeout=Duration.seconds(120),
            # Debug settings
            debug_logging=self.env_config.name.value != "prod",
        )

        # Allow proxy to access the cluster
        self._cluster.connections.allow_from(
            proxy,
            ec2.Port.tcp(3306),
            description="Allow RDS Proxy to connect to Aurora",
        )

        return proxy

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出用于跨 Stack 引用。"""
        prefix = self.env_config.resource_prefix
        # (output_id, value, description, export_name)
        outputs: list[tuple[str, str, str, str]] = [
            (
                "ClusterEndpoint",
                self._cluster.cluster_endpoint.hostname,
                "Aurora cluster writer endpoint",
                f"{prefix}-aurora-endpoint",
            ),
            (
                "ReaderEndpoint",
                self._cluster.cluster_read_endpoint.hostname,
                "Aurora cluster reader endpoint",
                f"{prefix}-aurora-reader-endpoint",
            ),
            (
                "Port",
                str(self._cluster.cluster_endpoint.port),
                "Aurora cluster port",
                f"{prefix}-aurora-port",
            ),
        ]
        if self._secret:
            outputs.append(
                (
                    "SecretArn",
                    self._secret.secret_arn,
                    "Secrets Manager secret ARN for database credentials",
                    f"{prefix}-aurora-secret-arn",
                )
            )
        if self._proxy:
            outputs.append(
                (
                    "ProxyEndpoint",
                    self._proxy.endpoint,
                    "RDS Proxy endpoint",
                    f"{prefix}-aurora-proxy-endpoint",
                )
            )
        outputs.append(
            (
                "SecurityGroupId",
                self._security_group.security_group_id,
                "Aurora security group ID",
                f"{prefix}-aurora-sg-id",
            )
        )

        for output_id, value, description, export_name in outputs:
            create_output(self, output_id, value, description, export_name=export_name)

    @property
    def cluster(self) -> rds.DatabaseCluster:
        return self._cluster

    @property
    def proxy(self) -> rds.DatabaseProxy | None:
        return self._proxy

    @property
    def security_group(self) -> ec2.SecurityGroup:
        return self._security_group

    @property
    def secret(self) -> secretsmanager.ISecret | None:
        return self._secret

    @property
    def connection_string_secret_key(self) -> str:
        return "connectionString"
