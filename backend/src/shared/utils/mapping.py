"""Bidirectional enum mapper for Domain ↔ API enum conversion."""

from enum import Enum
from typing import TypeVar, overload

DomainEnumT = TypeVar("DomainEnumT", bound=Enum)
ApiEnumT = TypeVar("ApiEnumT", bound=Enum)
EnumT = TypeVar("EnumT", bound=Enum)


class EnumMapper:
    """Bidirectional mapper between Domain enums and API enums.

    Supports both conventions:
    - UPPERCASE domain (JobStatus.RUNNING = "RUNNING") ↔ lowercase API ("running")
    - Same-case domain (LimitRole.ADMIN = "admin") ↔ API ("admin")
    """

    @staticmethod
    def to_api(domain_enum: DomainEnumT | None, api_enum_class: type[ApiEnumT]) -> ApiEnumT | None:
        """Convert Domain enum to API enum.

        Tries exact value match first, then lowercase conversion.

        Example:
            JobStatus.RUNNING (value: "RUNNING") → JobStatusEnum.RUNNING (value: "running")
            LimitRole.ADMIN (value: "admin") → LimitRoleEnum.ADMIN (value: "admin")
        """
        if domain_enum is None:
            return None
        # 先尝试精确值匹配（同大小写枚举）
        try:
            return api_enum_class(domain_enum.value)
        except ValueError:
            pass
        # 回退到小写匹配（大写 Domain → 小写 API）
        return api_enum_class(domain_enum.value.lower())

    @staticmethod
    def to_domain(api_enum: ApiEnumT | None, domain_enum_class: type[DomainEnumT]) -> DomainEnumT | None:
        """Convert API enum to Domain enum.

        Tries exact value match first, then uppercase conversion.
        Handles both UPPERCASE domain enums (e.g. JobStatus.RUNNING = "RUNNING")
        and lowercase domain enums (e.g. LimitRole.ADMIN = "admin").

        Example:
            JobStatusEnum.RUNNING → JobStatus.RUNNING (value: "RUNNING")
            LimitRoleEnum.ADMIN → LimitRole.ADMIN (value: "admin")
        """
        if api_enum is None:
            return None
        # 先尝试精确值匹配（适用于同大小写的枚举）
        try:
            return domain_enum_class(api_enum.value)
        except ValueError:
            pass
        # 回退到大写匹配（适用于 API 小写 → Domain 大写的枚举）
        try:
            return domain_enum_class(api_enum.value.upper())
        except ValueError:
            pass
        # 按名称匹配
        try:
            return domain_enum_class[api_enum.name]
        except KeyError:
            return None

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

    @overload
    @staticmethod
    def from_string(
        value: str | None,
        enum_class: type[EnumT],
        default: EnumT,
    ) -> EnumT: ...

    @overload
    @staticmethod
    def from_string(
        value: str | None,
        enum_class: type[EnumT],
        default: None = None,
    ) -> EnumT | None: ...

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
