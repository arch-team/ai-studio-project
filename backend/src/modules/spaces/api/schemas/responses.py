"""Space API response schemas."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.shared.api.schemas import EntitySchema

if TYPE_CHECKING:
    from src.modules.spaces.domain.entities import Space  # noqa: F401


class SpaceInstanceTypeEnum(str, Enum):
    """Space instance type enum for API."""

    ML_T3_MEDIUM = "ml.t3.medium"
    ML_T3_LARGE = "ml.t3.large"
    ML_G4DN_XLARGE = "ml.g4dn.xlarge"
    ML_G5_XLARGE = "ml.g5.xlarge"
    ML_G5_2XLARGE = "ml.g5.2xlarge"


class SpaceTypeEnum(str, Enum):
    """Space IDE type enum for API."""

    JUPYTER = "jupyter"
    VSCODE = "vscode"
    RSTUDIO = "rstudio"


class SpaceStatusEnum(str, Enum):
    """Space status enum for API."""

    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DELETED = "deleted"


class SpaceSummary(EntitySchema["Space"]):
    """Space summary for list responses.

    枚举映射由 EntitySchema 自动从字段类型推断。
    """

    id: str
    space_name: str
    owner_id: int
    instance_type: SpaceInstanceTypeEnum
    space_type: SpaceTypeEnum
    status: SpaceStatusEnum
    created_at: datetime


class SpaceDetail(SpaceSummary):
    """Space detail response - 继承 SpaceSummary 扩展更多字段."""

    storage_size_gb: int
    lifecycle_config_arn: str | None = None
    sagemaker_space_arn: str | None = None
    updated_at: datetime
    deleted_at: datetime | None = None

    # 继承父类的枚举映射，无需重复声明


class SpaceListResponse(BaseModel):
    """Paginated list of spaces."""

    items: list[SpaceSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class SpaceAccessUrlResponse(BaseModel):
    """Space IDE 免登录访问 URL（约 5 分钟内有效，仅供即时跳转）."""

    url: str


class SpaceErrorResponse(BaseModel):
    """Space operation error response."""

    code: str
    message: str
    details: dict | None = None
