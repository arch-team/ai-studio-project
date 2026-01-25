"""DatasetModel ORM 模型 - 数据集元数据存储。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.datasets.domain.value_objects import (
    DatasetStatus,
    DatasetStorageType,
    DatasetType,
    DatasetVisibility,
)
from src.shared.infrastructure.database import Base
from src.shared.infrastructure.models import TimestampMixin

if TYPE_CHECKING:
    from src.modules.auth.infrastructure.models import UserModel
    from src.modules.datasets.infrastructure.models.upload_session_model import (
        UploadSessionModel,
    )


class DatasetModel(Base, TimestampMixin):
    """数据集 ORM 模型。"""

    __tablename__ = "datasets"

    # === 主键 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="数据集ID",
    )

    # === 数据集标识 ===
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="数据集名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="数据集描述",
    )
    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="v1",
        comment="数据集版本",
    )

    # === 存储位置 ===
    storage_type: Mapped[DatasetStorageType] = mapped_column(
        Enum(DatasetStorageType),
        nullable=False,
        default=DatasetStorageType.FSX,
        comment="存储类型",
    )
    storage_uri: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="存储 URI",
    )

    # === 数据集统计 ===
    total_size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="总大小(字节)",
    )
    file_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="文件数量",
    )

    # === 数据集类型 ===
    dataset_type: Mapped[DatasetType] = mapped_column(
        Enum(DatasetType),
        nullable=False,
        comment="数据集类型",
    )
    data_format: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="数据格式",
    )

    # === 数据集标签 ===
    tags: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="数据集标签",
    )

    # === 访问权限 ===
    visibility: Mapped[DatasetVisibility] = mapped_column(
        Enum(DatasetVisibility),
        nullable=False,
        default=DatasetVisibility.PRIVATE,
        comment="可见性",
    )
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所有者用户ID",
    )

    # === 数据集状态 ===
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(DatasetStatus),
        nullable=False,
        default=DatasetStatus.PREPARING,
        index=True,
        comment="数据集状态",
    )

    # === 访问时间 ===
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="最后访问时间",
    )

    # === 关系 ===
    owner: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="datasets",
    )
    upload_sessions: Mapped[list["UploadSessionModel"]] = relationship(
        "UploadSessionModel",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )

    __table_args__ = ({"comment": "数据集表"},)
