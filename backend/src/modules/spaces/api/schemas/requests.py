"""Space API request schemas."""

from enum import Enum

from pydantic import BaseModel, Field


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


class SpaceBackendEnum(str, Enum):
    """Space backend type enum for API."""

    STUDIO = "studio"
    HYPERPOD = "hyperpod"


class CreateSpaceRequest(BaseModel):
    """Request body for creating a development space."""

    space_name: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Space name",
    )
    instance_type: SpaceInstanceTypeEnum = Field(
        default=SpaceInstanceTypeEnum.ML_G5_XLARGE,
        description="Instance type for the space",
    )
    space_type: SpaceTypeEnum = Field(
        default=SpaceTypeEnum.JUPYTER,
        description="IDE type (jupyter, vscode, rstudio)",
    )
    backend: SpaceBackendEnum = Field(
        default=SpaceBackendEnum.STUDIO,
        description="Backend type (studio: SageMaker Studio, hyperpod: HyperPod native)",
    )
    storage_size_gb: int = Field(
        default=20,
        ge=5,
        le=500,
        description="Storage size in GB",
    )


class UpdateSpaceRequest(BaseModel):
    """Request body for updating a development space."""

    space_name: str | None = Field(
        None,
        min_length=3,
        max_length=255,
        description="Space name",
    )
    instance_type: SpaceInstanceTypeEnum | None = Field(
        None,
        description="Instance type for the space",
    )
