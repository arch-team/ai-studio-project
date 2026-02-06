"""统一的实体-模式转换基类."""

from collections.abc import Callable
from enum import Enum
from typing import Any, ClassVar, Generic, Self, TypeVar, get_args, get_origin

from pydantic import BaseModel, ConfigDict

from src.shared.utils.mapping import EnumMapper

Entity = TypeVar("Entity")


class EntitySchema(BaseModel, Generic[Entity]):
    """统一的实体-模式转换基类，支持自动和手动映射。

    V2 优化版本特性：
    - 自动映射同名字段（默认启用）
    - 自动从字段类型注解推断枚举映射（无需手动声明 _enum_mappings）
    - 自动继承父类的枚举映射（Detail 继承 Summary 无需重复声明）
    - 通过 _custom_mappings 支持自定义字段转换
    - 支持模式继承（Summary/Detail 模式）
    - 性能优化的 ConfigDict 配置
    - 快速路径方法 from_entity_fast（跳过验证）

    示例 1 - 自动推断模式（推荐，V2 新特性）：
        class TrainingJobSummary(EntitySchema["TrainingJob"]):
            id: int
            job_name: str
            status: JobStatusEnum      # 自动推断枚举映射！
            priority: JobPriorityEnum  # 自动推断枚举映射！

        # Detail 继承 Summary，自动继承枚举映射
        class TrainingJobDetail(TrainingJobSummary):
            description: str | None
            distribution_strategy: DistributionStrategyEnum  # 自动推断！

    示例 2 - 显式枚举映射（向后兼容）：
        class CustomSchema(EntitySchema["Entity"]):
            status: str  # API 返回字符串

            # 显式映射优先级高于自动推断
            _enum_mappings: ClassVar[dict[str, type[Enum]]] = {
                "status": StatusEnum,
            }

    示例 3 - 自定义映射（用于复杂转换）：
        class ComplexSchema(EntitySchema["ComplexEntity"]):
            computed_field: str

            _custom_mappings: ClassVar[dict[str, Callable[[Any], Any]]] = {
                "computed_field": lambda e: f"{e.first}_{e.last}",
            }

    使用：
        summary = TrainingJobSummary.from_entity(job)
        detail = TrainingJobDetail.from_entity(job, owner_username="alice")
        # 批量快速转换（跳过验证，仅用于可信 ORM 数据）
        summaries = TrainingJobSummary.from_entity_list_fast(jobs)
    """

    # Pydantic V2 性能优化配置
    model_config = ConfigDict(
        from_attributes=True,  # 支持 ORM 模型转换
        validate_default=False,  # 跳过默认值验证，提升性能
    )

    # 子类可覆盖的类属性
    _auto_mapping: ClassVar[bool] = True  # 是否启用自动映射
    _enum_mappings: ClassVar[dict[str, type[Enum]]] = {}  # 显式枚举映射（优先级高于自动推断）
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
        raise NotImplementedError(f"{cls.__name__} 必须实现 _map_entity_fields() 或启用 _auto_mapping")

    @classmethod
    def _get_all_enum_mappings(cls) -> dict[str, type[Enum]]:
        """收集当前类和所有父类的枚举映射。

        自动合并继承链中的 _enum_mappings，子类映射优先级更高。
        """
        result: dict[str, type[Enum]] = {}

        # 从基类开始收集，子类覆盖父类
        for base in reversed(cls.__mro__):
            if hasattr(base, "_enum_mappings") and base._enum_mappings:
                result.update(base._enum_mappings)

        return result

    @classmethod
    def _infer_enum_from_annotation(cls, field_name: str) -> type[Enum] | None:
        """从字段类型注解推断枚举类型。支持直接枚举和 Optional[Enum] 类型。"""
        field_info = cls.model_fields.get(field_name)
        if not field_info or field_info.annotation is None:
            return None
        return cls._extract_enum_from_type(field_info.annotation)

    @classmethod
    def _extract_enum_from_type(cls, annotation: Any) -> type[Enum] | None:
        """从类型注解中提取枚举类型。"""
        # 直接是枚举类型
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return annotation
        # 处理 Union 类型（Enum | None 或 Optional[Enum]）
        if get_origin(annotation) is not None:
            return next(
                (arg for arg in get_args(annotation) if isinstance(arg, type) and issubclass(arg, Enum)),
                None,
            )
        return None

    @classmethod
    def _get_all_custom_mappings(cls) -> dict[str, Callable[[Any], Any]]:
        """收集当前类和所有父类的自定义映射。"""
        result: dict[str, Callable[[Any], Any]] = {}
        for base in reversed(cls.__mro__):
            if hasattr(base, "_custom_mappings") and base._custom_mappings:
                result.update(base._custom_mappings)
        return result

    @classmethod
    def _get_enum_type(cls, field_name: str, enum_mappings: dict[str, type[Enum]]) -> type[Enum] | None:
        """获取字段的枚举类型（显式映射优先，否则自动推断）。"""
        return enum_mappings.get(field_name) or cls._infer_enum_from_annotation(field_name)

    @classmethod
    def _map_field_value(
        cls,
        field_name: str,
        entity: Entity,
        custom_mappings: dict[str, Callable[[Any], Any]],
        enum_mappings: dict[str, type[Enum]],
    ) -> tuple[bool, Any]:
        """映射单个字段值。返回 (是否有值, 值)。"""
        # 自定义映射优先
        if field_name in custom_mappings:
            return True, custom_mappings[field_name](entity)
        # 检查实体是否有该字段
        if not hasattr(entity, field_name):
            return False, None
        value = getattr(entity, field_name)
        # 枚举转换
        if value is not None:
            if enum_type := cls._get_enum_type(field_name, enum_mappings):
                value = EnumMapper.to_api(value, enum_type)
        return True, value

    @classmethod
    def _auto_map_fields(cls, entity: Entity) -> dict[str, Any]:
        """自动映射实体字段到模式。"""
        enum_mappings = cls._get_all_enum_mappings()
        custom_mappings = cls._get_all_custom_mappings()
        result: dict[str, Any] = {}

        for field_name in cls.model_fields:
            if field_name in cls._exclude_fields:
                continue
            has_value, value = cls._map_field_value(field_name, entity, custom_mappings, enum_mappings)
            if has_value:
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

    @classmethod
    def from_entity_fast(cls, entity: Entity, **extra_fields: Any) -> Self:
        """快速路径：从实体创建模式实例（跳过 Pydantic 验证）。

        警告：仅用于可信数据源（如 ORM 模型），不适用于用户输入。
        性能提升约 40-50%，但不会验证数据完整性。

        Args:
            entity: 领域实体实例
            **extra_fields: 额外字段

        Returns:
            带映射字段的模式实例（未验证）
        """
        if cls._auto_mapping:
            fields = cls._auto_map_fields(entity)
        else:
            fields = cls._map_entity_fields(entity)

        fields.update(extra_fields)
        return cls.model_construct(**fields)

    @classmethod
    def from_entity_list_fast(cls, entities: list[Entity], **extra_fields: Any) -> list[Self]:
        """快速路径：从实体列表批量创建模式实例（跳过验证）。

        警告：仅用于可信数据源，不适用于用户输入。

        Args:
            entities: 领域实体列表
            **extra_fields: 应用于所有实例的额外字段

        Returns:
            模式实例列表（未验证）
        """
        return [cls.from_entity_fast(entity, **extra_fields) for entity in entities]
