"""统一的实体-模式转换基类."""

from collections.abc import Callable
from enum import Enum
from typing import Any, ClassVar, Generic, Self, TypeVar

from pydantic import BaseModel

from src.shared.utils.mapping import EnumMapper

Entity = TypeVar("Entity")


class EntitySchema(BaseModel, Generic[Entity]):
    """统一的实体-模式转换基类，支持自动和手动映射。

    合并了原来的 EntitySchema 和 AutoMappingEntitySchema，
    提供灵活的映射策略。

    特性：
    - 自动映射同名字段（默认启用）
    - 通过 _enum_mappings 配置处理枚举转换
    - 通过 _custom_mappings 支持自定义字段转换
    - 支持模式继承（Summary/Detail 模式）
    - 可选的手动映射模式（覆盖 _map_entity_fields）

    示例 1 - 自动映射模式（推荐）：
        class TrainingJobSummary(EntitySchema["TrainingJob"]):
            id: int
            job_name: str
            status: JobStatusEnum
            priority: JobPriorityEnum

            _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
                "status": JobStatusEnum,
                "priority": JobPriorityEnum,
            }

        # Detail 继承 Summary，无重复
        class TrainingJobDetail(TrainingJobSummary):
            description: str | None
            owner_id: int

            _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
                **TrainingJobSummary._enum_mappings,
                "distribution_strategy": DistributionStrategyEnum,
            }

    示例 2 - 手动映射模式（用于复杂转换）：
        class ComplexSchema(EntitySchema["ComplexEntity"]):
            computed_field: str

            @classmethod
            def _map_entity_fields(cls, entity: ComplexEntity) -> dict:
                return {
                    "computed_field": f"{entity.first}_{entity.last}"
                }

    使用：
        summary = TrainingJobSummary.from_entity(job)
        detail = TrainingJobDetail.from_entity(job, owner_username="alice")
    """

    # 子类可覆盖的类属性
    _auto_mapping: ClassVar[bool] = True  # 是否启用自动映射
    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {}  # 枚举映射配置
    _custom_mappings: ClassVar[dict[str, Callable[[Any], Any]]] = {}  # 自定义字段映射
    _exclude_fields: ClassVar[set[str]] = set()  # 排除的字段

    @classmethod
    def from_entity(cls, entity: Entity, **extra_fields: Any) -> Self:
        """从领域实体创建模式实例。

        Args:
            entity: 领域实体实例
            **extra_fields: 实体上不存在的额外字段（如 owner_username）

        Returns:
            带映射字段的模式实例
        """
        if cls._auto_mapping:
            fields = cls._auto_map_fields(entity)
        else:
            fields = cls._map_entity_fields(entity)

        fields.update(extra_fields)
        return cls(**fields)

    @classmethod
    def _map_entity_fields(cls, entity: Entity) -> dict[str, Any]:
        """手动映射实体字段到模式字段。

        子类可以覆盖此方法来定义字段映射。
        使用 EnumMapper 进行枚举转换。

        仅在 _auto_mapping = False 时使用。
        """
        if cls._auto_mapping:
            return cls._auto_map_fields(entity)
        raise NotImplementedError(
            f"{cls.__name__} 必须实现 _map_entity_fields() 或启用 _auto_mapping"
        )

    @classmethod
    def _auto_map_fields(cls, entity: Entity) -> dict[str, Any]:
        """自动映射实体字段到模式。

        映射规则：
        1. 跳过 _exclude_fields 中的字段
        2. 应用 _custom_mappings（如果为字段定义）
        3. 应用 _enum_mappings 进行枚举转换
        4. 其他同名字段直接赋值
        """
        result: dict[str, Any] = {}

        # 获取所有声明的模式字段
        for field_name in cls.model_fields:
            # 跳过排除的字段
            if field_name in cls._exclude_fields:
                continue

            # 自定义映射优先
            if field_name in cls._custom_mappings:
                mapper = cls._custom_mappings[field_name]
                result[field_name] = mapper(entity)
                continue

            # 检查实体是否有该字段
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
        """从实体列表创建模式实例。

        Args:
            entities: 领域实体列表
            **extra_fields: 应用于所有实例的额外字段

        Returns:
            模式实例列表
        """
        return [cls.from_entity(entity, **extra_fields) for entity in entities]