"""Bidirectional enum mapper for Domain ↔ API enum conversion."""

from enum import Enum
from typing import TypeVar

DomainEnumT = TypeVar("DomainEnumT", bound=Enum)
ApiEnumT = TypeVar("ApiEnumT", bound=Enum)


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
        if domain_enum is None:
            return None
        api_value = domain_enum.value.lower()
        return api_enum_class(api_value)

    @staticmethod
    def to_domain(api_enum: ApiEnumT | None, domain_enum_class: type[DomainEnumT]) -> DomainEnumT | None:
        """Convert API enum to Domain enum (lowercase → UPPERCASE).

        Example:
            JobStatusEnum.RUNNING → JobStatus.RUNNING (value: "RUNNING")
        """
        if api_enum is None:
            return None
        domain_value = api_enum.value.upper()
        return domain_enum_class(domain_value)
