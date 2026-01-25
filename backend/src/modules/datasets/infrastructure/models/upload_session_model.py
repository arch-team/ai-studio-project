"""UploadSessionModel ORM 模型 - S3 分片上传会话追踪。"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.models import TimestampMixin

if TYPE_CHECKING:
    from src.modules.auth.infrastructure.models import UserModel
    from src.modules.datasets.infrastructure.models import DatasetModel


class UploadSessionStatus(PyEnum):
    """上传会话状态枚举。"""

    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETING = "COMPLETING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    FAILED = "FAILED"


class UploadSessionModel(Base, TimestampMixin):
    """上传会话 ORM 模型 - 支持跨会话断点续传。"""

    __tablename__ = "upload_sessions"

    # === 主键 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="上传会话ID",
    )

    # === 上传标识 ===
    upload_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        comment="S3 Multipart Upload ID",
    )
    dataset_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联数据集ID",
    )

    # === S3 存储信息 ===
    bucket: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="S3 桶名",
    )
    s3_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="S3 对象键",
    )

    # === 文件信息 ===
    filename: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="原始文件名",
    )
    content_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="application/octet-stream",
        comment="MIME 类型",
    )
    total_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="文件总大小(字节)",
    )
    part_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="分片大小(字节)",
    )

    # === 状态 ===
    status: Mapped[UploadSessionStatus] = mapped_column(
        Enum(UploadSessionStatus),
        nullable=False,
        default=UploadSessionStatus.INITIATED,
        index=True,
        comment="上传状态",
    )

    # === 分片追踪 ===
    completed_parts: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="已完成分片列表 (JSON)",
    )

    # === 进度统计 ===
    uploaded_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="已上传字节数",
    )
    completed_part_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="已完成分片数",
    )

    # === 所有者 ===
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="上传者用户ID",
    )

    # === 过期时间 ===
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="会话过期时间",
    )

    # === 关系 ===
    dataset: Mapped["DatasetModel"] = relationship(
        "DatasetModel",
        back_populates="upload_sessions",
    )
    owner: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="upload_sessions",
    )

    __table_args__ = ({"comment": "数据集上传会话表"},)
