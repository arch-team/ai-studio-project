"""Bidirectional enum mapper for Domain ↔ API enum conversion."""

from enum import Enum
from typing import TypeVar

DomainEnumT = TypeVar("DomainEnumT", bound=Enum)
ApiEnumT = TypeVar("ApiEnumT", bound=Enum)
EnumT = TypeVar("EnumT", bound=Enum)


class EnumMapper:
    """Bidirectional mapper between Domain enums (UPPERCASE) and API enums (lowercase).

    Domain enums use UPPERCASE values (e.g., JobStatus.RUNNING = "RUNNING")
    API enums use lowercase values (e.g., JobStatusEnum.RUNNING = "running")
    """

    @staticmethod
    def to_api(domain_enum: DomainEnumT | None, api_enum_class: type[ApiEnumT]) -> ApiEnumT | None:
        """Convert Domain enum to API enum (UPPERCASE → lowercase).

        Example:
            JobStatus.RUNNING → JobStatusEnum.RUNNING (value: "running")
        """
        return api_enum_class(domain_enum.value.lower()) if domain_enum else None

    @staticmethod
    def to_domain(api_enum: ApiEnumT | None, domain_enum_class: type[DomainEnumT]) -> DomainEnumT | None:
        """Convert API enum to Domain enum (lowercase → UPPERCASE).

        Example:
            JobStatusEnum.RUNNING → JobStatus.RUNNING (value: "RUNNING")
        """
        return domain_enum_class(api_enum.value.upper()) if api_enum else None

    @staticmethod
    def model_to_domain(
        model_enum: ApiEnumT | None,
        domain_class: type[DomainEnumT],
    ) -> DomainEnumT | None:
        """Convert ORM Model enum to Domain enum (same value format).

        Use this in repository _to_entity() methods.

        Example:
            JobStatusModel.RUNNING → JobStatus.RUNNING
        """
        return domain_class(model_enum.value) if model_enum else None

    @staticmethod
    def domain_to_model(
        domain_enum: DomainEnumT | None,
        model_class: type[ApiEnumT],
    ) -> ApiEnumT | None:
        """Convert Domain enum to ORM Model enum (same value format).

        Use this in repository _to_model() methods.

        Example:
            JobStatus.RUNNING → JobStatusModel.RUNNING
        """
        return model_class(domain_enum.value) if domain_enum else None

    @staticmethod
    def from_string(
        value: str | None,
        enum_class: type[EnumT],
        default: EnumT | None = None,
    ) -> EnumT | None:
        """Convert string to Domain enum (case-insensitive).

        Tries to match by enum name first (e.g., "ddp" → DDP), then by value.

        Args:
            value: String value to convert (case-insensitive)
            enum_class: Target enum class
            default: Default value if conversion fails

        Returns:
            Matching enum member or default

        Example:
            from_string("ddp", DistributionStrategy) → DistributionStrategy.DDP
            from_string("DDP", DistributionStrategy) → DistributionStrategy.DDP
        """
        if value is None:
            return default

        upper_value = value.upper()

        # Try matching by name
        try:
            return enum_class[upper_value]
        except KeyError:
            pass

        # Try matching by value
        for member in enum_class:
            if member.value.upper() == upper_value:
                return member

        return default
