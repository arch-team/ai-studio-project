"""JobTemplate ORM model - Reusable training configuration templates."""

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

from src.modules.training.domain.value_objects import TemplateVisibility
from src.shared.infrastructure.database import Base
from src.shared.infrastructure.models import TimestampMixin

if TYPE_CHECKING:
    from src.modules.auth.infrastructure.models import UserModel


class JobTemplateModel(Base, TimestampMixin):
    """Job template ORM model."""

    __tablename__ = "job_templates"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="模板ID")

    # Template identification
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True, comment="模板名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="模板描述")

    # Owner
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="所有者用户ID"
    )

    # Visibility
    visibility: Mapped[TemplateVisibility] = mapped_column(
        Enum(TemplateVisibility), nullable=False, default=TemplateVisibility.PRIVATE, index=True, comment="可见性范围"
    )

    # Training configuration (JSON blob)
    training_config: Mapped[dict] = mapped_column(JSON, nullable=False, comment="训练配置")

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="使用次数")
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True, comment="最后使用时间"
    )

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True, index=True, comment="软删除时间"
    )

    # Relationships
    owner: Mapped["UserModel"] = relationship("UserModel", back_populates="job_templates")

    __table_args__ = ({"comment": "任务模板表"},)
