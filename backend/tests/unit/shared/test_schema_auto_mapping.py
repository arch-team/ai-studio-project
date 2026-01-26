"""Unit tests for EntitySchema (auto-mapping)."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import ClassVar

from src.shared.api.schemas.entity_schema import EntitySchema


# 测试用的 Domain 枚举
class DomainStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class DomainPriority(Enum):
    HIGH = "HIGH"
    LOW = "LOW"


# 测试用的 API 枚举
class ApiStatusEnum(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ApiPriorityEnum(Enum):
    HIGH = "high"
    LOW = "low"


# 测试用的 Entity
@dataclass
class SampleEntity:
    id: int
    name: str
    status: DomainStatus
    priority: DomainPriority
    score: Decimal | None = None
    created_at: datetime = field(default_factory=datetime.now)
    description: str | None = None


class TestAutoMappingBasic:
    """Tests for basic auto-mapping functionality."""

    def test_auto_maps_same_name_fields(self):
        """同名字段自动映射。"""

        class SimpleSchema(EntitySchema["SampleEntity"]):
            id: int
            name: str

        entity = SampleEntity(
            id=1,
            name="test",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
        )

        result = SimpleSchema.from_entity(entity)

        assert result.id == 1
        assert result.name == "test"

    def test_skips_fields_not_in_entity(self):
        """Schema 中有但 Entity 中没有的字段不会报错。"""

        class SchemaWithExtraField(EntitySchema["SampleEntity"]):
            id: int
            name: str
            extra_field: str | None = None  # Entity 中不存在

        entity = SampleEntity(
            id=1,
            name="test",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
        )

        result = SchemaWithExtraField.from_entity(entity)

        assert result.id == 1
        assert result.extra_field is None

    def test_extra_fields_override_entity(self):
        """extra_fields 参数可覆盖自动映射。"""

        class SimpleSchema(EntitySchema["SampleEntity"]):
            id: int
            name: str

        entity = SampleEntity(
            id=1,
            name="original",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
        )

        result = SimpleSchema.from_entity(entity, name="overridden")

        assert result.name == "overridden"


class TestEnumMapping:
    """Tests for enum conversion via _enum_mappings."""

    def test_converts_enum_via_mapping(self):
        """枚举通过 _enum_mappings 配置自动转换。"""

        class SchemaWithEnum(EntitySchema["SampleEntity"]):
            id: int
            status: ApiStatusEnum

            _enum_mappings: ClassVar[dict] = {"status": ApiStatusEnum}

        entity = SampleEntity(
            id=1,
            name="test",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
        )

        result = SchemaWithEnum.from_entity(entity)

        assert result.status == ApiStatusEnum.ACTIVE
        assert result.status.value == "active"

    def test_multiple_enum_mappings(self):
        """多个枚举字段同时转换。"""

        class SchemaWithMultipleEnums(EntitySchema["SampleEntity"]):
            id: int
            status: ApiStatusEnum
            priority: ApiPriorityEnum

            _enum_mappings: ClassVar[dict] = {
                "status": ApiStatusEnum,
                "priority": ApiPriorityEnum,
            }

        entity = SampleEntity(
            id=1,
            name="test",
            status=DomainStatus.INACTIVE,
            priority=DomainPriority.LOW,
        )

        result = SchemaWithMultipleEnums.from_entity(entity)

        assert result.status == ApiStatusEnum.INACTIVE
        assert result.priority == ApiPriorityEnum.LOW

    def test_none_enum_value_stays_none(self):
        """枚举值为 None 时保持 None。"""

        @dataclass
        class EntityWithOptionalEnum:
            id: int
            status: DomainStatus | None = None

        class SchemaWithOptionalEnum(EntitySchema["EntityWithOptionalEnum"]):
            id: int
            status: ApiStatusEnum | None = None

            _enum_mappings: ClassVar[dict] = {"status": ApiStatusEnum}

        entity = EntityWithOptionalEnum(id=1, status=None)

        result = SchemaWithOptionalEnum.from_entity(entity)

        assert result.status is None


class TestCustomMapping:
    """Tests for custom field mappings via _custom_mappings."""

    def test_custom_mapping_function(self):
        """自定义映射函数覆盖默认行为。"""

        class SchemaWithCustomMapping(EntitySchema["SampleEntity"]):
            id: int
            full_name: str  # 自定义字段名

            _custom_mappings: ClassVar[dict] = {
                "full_name": lambda e: f"Name: {e.name}",
            }

        entity = SampleEntity(
            id=1,
            name="test",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
        )

        result = SchemaWithCustomMapping.from_entity(entity)

        assert result.full_name == "Name: test"

    def test_custom_mapping_takes_precedence(self):
        """自定义映射优先于枚举映射和默认映射。"""

        class SchemaWithCustomOverride(EntitySchema["SampleEntity"]):
            id: int
            name: str

            _custom_mappings: ClassVar[dict] = {
                "name": lambda e: e.name.upper(),
            }

        entity = SampleEntity(
            id=1,
            name="test",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
        )

        result = SchemaWithCustomOverride.from_entity(entity)

        assert result.name == "TEST"


class TestExcludeFields:
    """Tests for _exclude_fields functionality."""

    def test_excluded_fields_not_mapped(self):
        """排除的字段不会自动映射。"""

        class SchemaWithExclusion(EntitySchema["SampleEntity"]):
            id: int
            name: str | None = None  # 可选，因为被排除

            _exclude_fields: ClassVar[set] = {"name"}

        entity = SampleEntity(
            id=1,
            name="should_be_excluded",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
        )

        result = SchemaWithExclusion.from_entity(entity)

        assert result.id == 1
        assert result.name is None  # 被排除，使用默认值


class TestInheritance:
    """Tests for Schema inheritance pattern (Summary/Detail)."""

    def test_detail_inherits_summary_mappings(self):
        """Detail Schema 继承 Summary 的枚举映射。"""

        class SummarySchema(EntitySchema["SampleEntity"]):
            id: int
            name: str
            status: ApiStatusEnum

            _enum_mappings: ClassVar[dict] = {"status": ApiStatusEnum}

        class DetailSchema(SummarySchema):
            description: str | None
            priority: ApiPriorityEnum

            _enum_mappings: ClassVar[dict] = {
                **SummarySchema._enum_mappings,
                "priority": ApiPriorityEnum,
            }

        entity = SampleEntity(
            id=1,
            name="test",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
            description="A test entity",
        )

        summary = SummarySchema.from_entity(entity)
        detail = DetailSchema.from_entity(entity)

        # Summary 只有基本字段
        assert summary.id == 1
        assert summary.status == ApiStatusEnum.ACTIVE

        # Detail 继承 Summary 并扩展
        assert detail.id == 1
        assert detail.status == ApiStatusEnum.ACTIVE
        assert detail.priority == ApiPriorityEnum.HIGH
        assert detail.description == "A test entity"


class TestFromEntityList:
    """Tests for from_entity_list() method."""

    def test_converts_list_of_entities(self):
        """批量转换实体列表。"""

        class SimpleSchema(EntitySchema["SampleEntity"]):
            id: int
            name: str

        entities = [
            SampleEntity(id=1, name="first", status=DomainStatus.ACTIVE, priority=DomainPriority.HIGH),
            SampleEntity(id=2, name="second", status=DomainStatus.INACTIVE, priority=DomainPriority.LOW),
        ]

        results = SimpleSchema.from_entity_list(entities)

        assert len(results) == 2
        assert results[0].id == 1
        assert results[0].name == "first"
        assert results[1].id == 2
        assert results[1].name == "second"

    def test_empty_list_returns_empty(self):
        """空列表返回空列表。"""

        class SimpleSchema(EntitySchema["SampleEntity"]):
            id: int

        results = SimpleSchema.from_entity_list([])

        assert results == []


class TestComplexTypes:
    """Tests for complex type handling."""

    def test_decimal_preserved(self):
        """Decimal 类型保持精度。"""

        class SchemaWithDecimal(EntitySchema["SampleEntity"]):
            id: int
            score: Decimal | None

        entity = SampleEntity(
            id=1,
            name="test",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
            score=Decimal("3.14159"),
        )

        result = SchemaWithDecimal.from_entity(entity)

        assert result.score == Decimal("3.14159")

    def test_datetime_preserved(self):
        """datetime 类型保持完整。"""

        class SchemaWithDatetime(EntitySchema["SampleEntity"]):
            id: int
            created_at: datetime

        now = datetime(2024, 1, 15, 10, 30, 0)
        entity = SampleEntity(
            id=1,
            name="test",
            status=DomainStatus.ACTIVE,
            priority=DomainPriority.HIGH,
            created_at=now,
        )

        result = SchemaWithDatetime.from_entity(entity)

        assert result.created_at == now
