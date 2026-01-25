"""HyperPodCluster ORM model."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String, text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.modules.monitoring.domain.value_objects import ClusterStatus, HealthStatus
from src.shared.infrastructure.database import Base


class HyperPodClusterModel(Base):
    """HyperPod 集群 ORM 模型.

    映射 hyperpod_clusters 表，作为 HyperPod API 的本地缓存。
    """

    __tablename__ = "hyperpod_clusters"

    # Primary key
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="集群ID",
    )

    # Cluster identification
    cluster_name: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        comment="集群名称",
    )
    cluster_arn: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        comment="集群 ARN",
    )
    region: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="AWS 区域",
    )
    vpc_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="VPC ID",
    )

    # Instance configuration
    instance_groups: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        comment="实例组配置 JSON",
    )

    # Resource capacity
    total_nodes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="总节点数",
    )
    available_nodes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="可用节点数",
    )
    total_cpu_cores: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="总 CPU 核心数",
    )
    total_gpu_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="总 GPU 数量",
    )
    total_memory_gb: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="总内存 (GB)",
    )

    # Status fields
    status: Mapped[ClusterStatus] = mapped_column(
        Enum(ClusterStatus),
        nullable=False,
        server_default="creating",
        index=True,
        comment="集群状态",
    )
    health_status: Mapped[HealthStatus | None] = mapped_column(
        Enum(HealthStatus),
        nullable=True,
        index=True,
        comment="健康状态",
    )

    # FSx integration
    fsx_filesystem_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="FSx 文件系统 ID",
    )
    fsx_mount_point: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="FSx 挂载点",
    )

    # Monitoring integration
    prometheus_endpoint: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Prometheus 端点",
    )
    grafana_workspace_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="Grafana 工作区 ID",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        comment="更新时间",
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后同步时间",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"HyperPodClusterModel(id={self.id}, "
            f"cluster_name={self.cluster_name!r}, "
            f"status={self.status.value!r})"
        )
