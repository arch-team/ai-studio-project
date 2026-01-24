"""Enhanced EntitySchema with automatic field mapping."""

from collections.abc import Callable
from enum import Enum
from typing import Any, ClassVar, Generic, Self, TypeVar

from pydantic import BaseModel

from src.shared.utils.mapping import EnumMapper

Entity = TypeVar("Entity")


class AutoMappingEntitySchema(BaseModel, Generic[Entity]):
    """EntitySchema with automatic same-name field mapping.

    Features:
    - Auto-maps fields with same name between Entity and Schema
    - Handles enum conversion via _enum_mappings configuration
    - Supports custom field transformations via _custom_mappings
    - Enables Schema inheritance for Summary/Detail pattern

    Example:
        class TrainingJobSummary(AutoMappingEntitySchema["TrainingJob"]):
            id: int
            job_name: str
            status: JobStatusEnum
            priority: JobPriorityEnum

            _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
                "status": JobStatusEnum,
                "priority": JobPriorityEnum,
            }

        # Detail inherits Summary, no duplication
        class TrainingJobDetail(TrainingJobSummary):
            description: str | None
            owner_id: int

            _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
                **TrainingJobSummary._enum_mappings,
                "distribution_strategy": DistributionStrategyEnum,
            }

        # Usage:
        summary = TrainingJobSummary.from_entity(job)
        detail = TrainingJobDetail.from_entity(job, owner_username="alice")
    """

    # 子类可覆盖的类属性
    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {}
    _custom_mappings: ClassVar[dict[str, Callable[[Any], Any]]] = {}
    _exclude_fields: ClassVar[set[str]] = set()

    @classmethod
    def from_entity(cls, entity: Entity, **extra_fields: Any) -> Self:
        """Create schema instance from domain entity.

        Args:
            entity: Domain entity instance
            **extra_fields: Additional fields not on the entity

        Returns:
            Schema instance with mapped fields
        """
        fields = cls._auto_map_fields(entity)
        fields.update(extra_fields)
        return cls(**fields)

    @classmethod
    def _auto_map_fields(cls, entity: Entity) -> dict[str, Any]:
        """Auto-map fields from entity to schema.

        Mapping rules:
        1. Skip fields in _exclude_fields
        2. Apply _custom_mappings if defined for field
        3. Apply _enum_mappings for enum conversion
        4. Direct assignment for other same-name fields
        """
        result: dict[str, Any] = {}

        # 获取所有声明的 schema 字段
        for field_name in cls.model_fields:
            # 跳过排除的字段
            if field_name in cls._exclude_fields:
                continue

            # 自定义映射优先
            if field_name in cls._custom_mappings:
                mapper = cls._custom_mappings[field_name]
                result[field_name] = mapper(entity)
                continue

            # 检查 entity 是否有该字段
            if not hasattr(entity, field_name):
                continue

            value = getattr(entity, field_name)

            # 枚举转换
            if field_name in cls._enum_mappings and value is not None:
                api_enum_class = cls._enum_mappings[field_name]
                value = EnumMapper.to_api(value, api_enum_class)

            result[field_name] = value

        return result

    @classmethod
    def from_entity_list(cls, entities: list[Entity], **extra_fields: Any) -> list[Self]:
        """Create schema instances from a list of entities.

        Args:
            entities: List of domain entities
            **extra_fields: Additional fields applied to all instances

        Returns:
            List of schema instances
        """
        return [cls.from_entity(entity, **extra_fields) for entity in entities]
